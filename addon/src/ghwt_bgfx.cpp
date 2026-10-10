// ghwt_bgfx: ReShade 6.8 add-on for Guitar Hero World Tour: Definitive Edition (32-bit, Direct3D 9).
//
// Goal: apply the ReShade preset to the background only (venue, band, crowd) and only during songs and
// cutscenes, never on the HUD. It works by calling effect_runtime::render_effects() mid-frame, right before
// the first HUD draw, which also suppresses ReShade's usual end-of-frame pass.
//
// Phase 1 (this build) is the investigation tooling:
//   - Frame dump (F10, or the overlay button): one frame's draw list as CSV, plus a snapshot of the bound
//     render target every time the draw "segment" changes (render target, depth test, blending,
//     screen-space vertices), plus the final frame before and after effects. Written to
//     <game>\ghwt_bgfx_dumps\<timestamp>\.
//   - Scrub mode (F9): render effects right before draw N instead of at the end of the frame. PageUp and
//     PageDown move N by 1 (Shift: 25). Wherever the HUD stops being affected is the boundary.
// Settings live in ReShade.ini under [GHWT_BGFX].

#define ImTextureID ImU64
#include <imgui.h>
#include <reshade.hpp>
#include <d3d9.h>

#include <cstdio>
#include <ctime>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

using namespace reshade::api;

extern "C" __declspec(dllexport) const char *NAME = "Background-only shaders";
extern "C" __declspec(dllexport) const char *DESCRIPTION =
	"GHWT:DE: applies the ReShade preset to the venue, band and crowd during songs and cutscenes, never to the HUD.";

namespace
{
	// ---- config (ReShade.ini [GHWT_BGFX]) ----
	// Release default: the investigation tooling (frame dump, scrub, trigger file) is off. Debug=1 in
	// [GHWT_BGFX] turns it on with F10 / F9 (DumpKey / ScrubKey override them).
	bool g_debug = false;
	uint32_t g_key_dump = 0;
	uint32_t g_key_scrub = 0;
	uint32_t g_max_snapshots = 64;

	// ---- shader / vertex declaration identity, filled from init_pipeline ----
	std::mutex g_map_mutex;
	std::unordered_map<uint64_t, uint32_t> g_shader_hash; // IDirect3D{Pixel,Vertex}Shader9* -> FNV-1a of bytecode
	std::unordered_map<uint64_t, bool> g_decl_post;       // IDirect3DVertexDeclaration9* -> has POSITIONT

	uint32_t fnv1a(const void *data, size_t size)
	{
		uint32_t h = 2166136261u;
		for (size_t i = 0; i < size; ++i)
			h = (h ^ static_cast<const uint8_t *>(data)[i]) * 16777619u;
		return h;
	}

	uint32_t lookup_hash(const void *ptr)
	{
		if (ptr == nullptr)
			return 0;
		std::lock_guard<std::mutex> lock(g_map_mutex);
		const auto it = g_shader_hash.find(reinterpret_cast<uintptr_t>(ptr));
		return it != g_shader_hash.end() ? it->second : 0xFFFFFFFFu;
	}

	// ---- Auto mode (experimental) ----
	// The game renders the scene off-screen and copies it to the back buffer with one full-screen draw (pixel
	// shader g_composite_ps). Everything drawn after that is 2D UI. Auto mode renders effects right after the
	// composite; frames without a composite get no effects.
	bool g_auto = true;
	uint32_t g_composite_ps = 0xDE796938;
	uint32_t g_cur_ps = 0;              // hash of the bound pixel shader (tracked from bind_pipeline)
	uint64_t g_cur_rt0 = 0;             // bound render target 0 (tracked from bind_render_targets_and_depth_stencil)
	bool g_composite_seen = false;      // the composite ran this frame
	bool g_pending_inject = false;      // inject before the next draw
	int g_inject_at = -1, g_inject_at_last = -1;

	// ---- Gate: songs and cutscenes only ----
	// Menus (song select, title, loading) draw their art through the same scene path and composite as the
	// venue, so structure alone can't tell them apart. Shader identity can:
	//  - ScenePS: shaders that only run when a venue is rendered (the venue's post chain entry and the
	//    sub-scene composite). They run before the composite, so the decision is made in the same frame.
	//  - GameplayPS: highway/gem shaders. Drawn after the composite, so they keep the gate open for
	//    GameplayHoldFrames frames as a backup.
	bool g_gate = true;
	std::vector<uint32_t> g_scene_ps = { 0xE5555C99, 0x850F299B };
	std::vector<uint32_t> g_gameplay_ps = { 0xFE74FFEA, 0x12827EBF, 0x5DBF7AEB };
	uint32_t g_gameplay_hold_frames = 30;
	bool g_scene_seen = false, g_gameplay_seen = false;
	uint32_t g_gameplay_hold = 0;
	bool g_gate_open_last = false;

	bool contains(const std::vector<uint32_t> &v, uint32_t x)
	{
		for (uint32_t e : v)
			if (e == x)
				return true;
		return false;
	}

	bool gate_open()
	{
		return !g_gate || g_scene_seen || g_gameplay_hold != 0;
	}

	// ---- per-frame state ----
	effect_runtime *g_runtime = nullptr;
	uint32_t g_draw_index = 0;      // draws so far this frame
	uint32_t g_draws_last_frame = 0;
	bool g_injected_this_frame = false;

	bool g_scrub = false;
	uint32_t g_scrub_n = 0;
	uint32_t g_scrub_ps = 0, g_scrub_vs = 0; // shaders bound at draw N (last frame it was reached)

	// ---- dump state ----
	bool g_dump_armed = false;   // set by the key, the dump starts at the next frame boundary
	bool g_dump_active = false;  // capturing the current frame
	std::string g_dump_dir;
	std::string g_last_dump;
	FILE *g_csv = nullptr;
	uint32_t g_snapshots = 0;
	uint64_t g_last_segment = ~0ull;
	std::unordered_map<uintptr_t, int> g_rt_ids;

	IDirect3DDevice9 *native(command_list *cmd_list)
	{
		return reinterpret_cast<IDirect3DDevice9 *>(cmd_list->get_device()->get_native());
	}

	std::string game_dir()
	{
		char path[MAX_PATH] = {};
		GetModuleFileNameA(nullptr, path, MAX_PATH);
		std::string s(path);
		return s.substr(0, s.find_last_of("\\/"));
	}

	// ---- image output (BMP, no dependencies) ----
	bool write_bmp(const std::string &file, uint32_t w, uint32_t h, const std::vector<uint8_t> &bgr)
	{
		FILE *f = nullptr;
		if (fopen_s(&f, file.c_str(), "wb") != 0 || f == nullptr)
			return false;
		const uint32_t row = (w * 3 + 3) & ~3u;
		const uint32_t data_size = row * h;
		uint8_t hdr[54] = { 'B', 'M' };
		*reinterpret_cast<uint32_t *>(hdr + 2) = 54 + data_size;
		*reinterpret_cast<uint32_t *>(hdr + 10) = 54;
		*reinterpret_cast<uint32_t *>(hdr + 14) = 40;
		*reinterpret_cast<int32_t *>(hdr + 18) = static_cast<int32_t>(w);
		*reinterpret_cast<int32_t *>(hdr + 22) = static_cast<int32_t>(h);
		*reinterpret_cast<uint16_t *>(hdr + 26) = 1;
		*reinterpret_cast<uint16_t *>(hdr + 28) = 24;
		*reinterpret_cast<uint32_t *>(hdr + 34) = data_size;
		fwrite(hdr, 1, sizeof(hdr), f);
		std::vector<uint8_t> line(row, 0);
		for (uint32_t y = 0; y < h; ++y)
		{
			memcpy(line.data(), bgr.data() + static_cast<size_t>(h - 1 - y) * w * 3, w * 3);
			fwrite(line.data(), 1, row, f);
		}
		fclose(f);
		return true;
	}

	float half_to_float(uint16_t v)
	{
		const uint32_t s = (v & 0x8000u) << 16, e = (v >> 10) & 0x1F, m = v & 0x3FF;
		uint32_t bits;
		if (e == 0)
			bits = s; // flush denormals; good enough for a preview
		else if (e == 31)
			bits = s | 0x7F800000u | (m << 13);
		else
			bits = s | ((e + 112) << 23) | (m << 13);
		float f;
		memcpy(&f, &bits, 4);
		return f;
	}

	uint8_t to_u8(float f)
	{
		f = f < 0 ? 0 : (f > 1 ? 1 : f);
		return static_cast<uint8_t>(f * 255.0f + 0.5f);
	}

	// Copies a render-target surface to system memory and writes it as a BMP, downscaled by 'div'.
	// Returns a short status string for the CSV.
	std::string snapshot_surface(IDirect3DDevice9 *dev, IDirect3DSurface9 *rt, const std::string &file, uint32_t div)
	{
		D3DSURFACE_DESC desc = {};
		if (rt == nullptr || FAILED(rt->GetDesc(&desc)))
			return "no-rt";
		if (desc.MultiSampleType != D3DMULTISAMPLE_NONE)
			return "msaa-skipped";
		if (desc.Format != D3DFMT_A8R8G8B8 && desc.Format != D3DFMT_X8R8G8B8 && desc.Format != D3DFMT_A16B16G16R16F)
			return "fmt-" + std::to_string(desc.Format) + "-skipped";

		IDirect3DSurface9 *sys = nullptr;
		if (FAILED(dev->CreateOffscreenPlainSurface(desc.Width, desc.Height, desc.Format, D3DPOOL_SYSTEMMEM, &sys, nullptr)))
			return "alloc-failed";
		std::string status = "ok";
		D3DLOCKED_RECT lr = {};
		if (FAILED(dev->GetRenderTargetData(rt, sys)))
			status = "readback-failed";
		else if (FAILED(sys->LockRect(&lr, nullptr, D3DLOCK_READONLY)))
			status = "lock-failed";
		else
		{
			const uint32_t w = desc.Width / div, h = desc.Height / div;
			std::vector<uint8_t> bgr(static_cast<size_t>(w) * h * 3);
			for (uint32_t y = 0; y < h; ++y)
			{
				const uint8_t *src = static_cast<const uint8_t *>(lr.pBits) + static_cast<size_t>(y * div) * lr.Pitch;
				for (uint32_t x = 0; x < w; ++x)
				{
					uint8_t *dst = &bgr[(static_cast<size_t>(y) * w + x) * 3];
					if (desc.Format == D3DFMT_A16B16G16R16F)
					{
						const uint16_t *p = reinterpret_cast<const uint16_t *>(src) + static_cast<size_t>(x * div) * 4;
						dst[0] = to_u8(half_to_float(p[2]));
						dst[1] = to_u8(half_to_float(p[1]));
						dst[2] = to_u8(half_to_float(p[0]));
					}
					else
					{
						const uint8_t *p = src + static_cast<size_t>(x * div) * 4; // B, G, R, A in memory
						dst[0] = p[0];
						dst[1] = p[1];
						dst[2] = p[2];
					}
				}
			}
			sys->UnlockRect();
			if (!write_bmp(file, w, h, bgr))
				status = "write-failed";
		}
		sys->Release();
		return status;
	}

	bool is_back_buffer(IDirect3DSurface9 *rt)
	{
		return g_runtime != nullptr && rt != nullptr &&
			g_runtime->get_current_back_buffer().handle == reinterpret_cast<uintptr_t>(rt);
	}

	// ---- mid-frame effect injection ----
	// render_effects() may change pipeline state and render targets, so save and restore them.
	// State blocks don't cover render targets or depth-stencil, so those are saved by hand.
	// Everything is released at the end, so nothing survives into a device Reset().
	void inject_effects(command_list *cmd_list)
	{
		if (g_runtime == nullptr || g_injected_this_frame)
			return;
		g_injected_this_frame = true;

		// Mirrors ReShade's own D3D9 state_block (source/d3d9/d3d9_impl_state_block.cpp): capture explicitly,
		// apply the block first, then render targets, depth-stencil and the two sRGB states (which ReShade notes
		// are not reliably restored by the block), and the viewport last.
		IDirect3DDevice9 *dev = native(cmd_list);
		IDirect3DStateBlock9 *sb = nullptr;
		if (FAILED(dev->CreateStateBlock(D3DSBT_ALL, &sb)))
			return;
		sb->Capture();
		DWORD rt_count = 1;
		D3DCAPS9 caps = {};
		if (SUCCEEDED(dev->GetDeviceCaps(&caps)))
			rt_count = caps.NumSimultaneousRTs > 4 ? 4 : caps.NumSimultaneousRTs;
		IDirect3DSurface9 *rts[4] = {}, *ds = nullptr;
		for (DWORD i = 0; i < rt_count; ++i)
			dev->GetRenderTarget(i, &rts[i]);
		dev->GetDepthStencilSurface(&ds);
		D3DVIEWPORT9 vp = {};
		dev->GetViewport(&vp);
		DWORD srgb_write = 0, srgb_texture = 0;
		dev->GetRenderState(D3DRS_SRGBWRITEENABLE, &srgb_write);
		dev->GetSamplerState(0, D3DSAMP_SRGBTEXTURE, &srgb_texture);

		const resource bb = g_runtime->get_current_back_buffer();
		// D3D9: the back-buffer surface is its own view, and ReShade marks the sRGB variant by setting bit 0
		// of the handle (d3d9_impl_device.cpp, create_resource_view). Passing the plain view for both made
		// passes with SRGBWriteEnable (PPFX_SSDO, AdaptiveTonemapper) write linear values: a darker image.
		const resource_view rtv = { bb.handle };
		const resource_view rtv_srgb = { bb.handle | 1ull };
		g_runtime->render_effects(cmd_list, rtv, rtv_srgb);

		sb->Apply();
		sb->Release(); // releases its references to the captured buffers and textures
		dev->SetRenderState(D3DRS_SRGBWRITEENABLE, srgb_write);
		dev->SetSamplerState(0, D3DSAMP_SRGBTEXTURE, srgb_texture);
		for (DWORD i = 0; i < rt_count; ++i)
		{
			dev->SetRenderTarget(i, rts[i]); // every slot, including empty ones an effect pass may have filled
			if (rts[i] != nullptr)
				rts[i]->Release();
		}
		dev->SetDepthStencilSurface(ds);
		if (ds != nullptr)
			ds->Release();
		dev->SetViewport(&vp); // after the render targets: SetRenderTarget resets the viewport
	}

	// ---- dump ----
	void begin_dump()
	{
		char stamp[32];
		const time_t t = time(nullptr);
		tm lt = {};
		localtime_s(&lt, &t);
		strftime(stamp, sizeof(stamp), "%Y%m%d-%H%M%S", &lt);
		const std::string root = game_dir() + "\\ghwt_bgfx_dumps";
		CreateDirectoryA(root.c_str(), nullptr);
		g_dump_dir = root + "\\" + stamp;
		CreateDirectoryA(g_dump_dir.c_str(), nullptr);

		if (fopen_s(&g_csv, (g_dump_dir + "\\draws.csv").c_str(), "w") != 0)
			g_csv = nullptr;
		if (g_csv != nullptr)
			fputs("idx,kind,count,ps,vs,rt0,rt0_bb,rt0_w,rt0_h,rt0_fmt,rt1,ds,zenable,zwrite,zfunc,blend,srcblend,dstblend,"
				"alphatest,cull,colorwrite,post,fvf,vp_x,vp_y,vp_w,vp_h,scissor,snapshot\n", g_csv);
		g_snapshots = 0;
		g_last_segment = ~0ull;
		g_rt_ids.clear();
		g_dump_active = true;
		reshade::log::message(reshade::log::level::info, ("ghwt_bgfx: dumping frame to " + g_dump_dir).c_str());
	}

	int rt_id(IDirect3DSurface9 *s)
	{
		if (s == nullptr)
			return -1;
		const auto it = g_rt_ids.find(reinterpret_cast<uintptr_t>(s));
		if (it != g_rt_ids.end())
			return it->second;
		const int id = static_cast<int>(g_rt_ids.size());
		g_rt_ids.emplace(reinterpret_cast<uintptr_t>(s), id);
		return id;
	}

	void dump_draw(command_list *cmd_list, const char *kind, uint32_t count)
	{
		IDirect3DDevice9 *dev = native(cmd_list);
		IDirect3DPixelShader9 *ps = nullptr;
		IDirect3DVertexShader9 *vs = nullptr;
		IDirect3DVertexDeclaration9 *decl = nullptr;
		IDirect3DSurface9 *rt0 = nullptr, *rt1 = nullptr, *ds = nullptr;
		dev->GetPixelShader(&ps);
		dev->GetVertexShader(&vs);
		dev->GetVertexDeclaration(&decl);
		dev->GetRenderTarget(0, &rt0);
		dev->GetRenderTarget(1, &rt1);
		dev->GetDepthStencilSurface(&ds);

		DWORD rs[9] = {};
		const D3DRENDERSTATETYPE states[9] = { D3DRS_ZENABLE, D3DRS_ZWRITEENABLE, D3DRS_ZFUNC, D3DRS_ALPHABLENDENABLE,
			D3DRS_SRCBLEND, D3DRS_DESTBLEND, D3DRS_ALPHATESTENABLE, D3DRS_CULLMODE, D3DRS_COLORWRITEENABLE };
		for (int i = 0; i < 9; ++i)
			dev->GetRenderState(states[i], &rs[i]);
		DWORD scissor = 0, fvf = 0;
		dev->GetRenderState(D3DRS_SCISSORTESTENABLE, &scissor);
		dev->GetFVF(&fvf);
		D3DVIEWPORT9 vp = {};
		dev->GetViewport(&vp);

		bool post = (fvf & D3DFVF_POSITION_MASK) == D3DFVF_XYZRHW;
		if (decl != nullptr)
		{
			std::lock_guard<std::mutex> lock(g_map_mutex);
			const auto it = g_decl_post.find(reinterpret_cast<uintptr_t>(decl));
			if (it != g_decl_post.end())
				post = post || it->second;
		}

		D3DSURFACE_DESC rd = {};
		if (rt0 != nullptr)
			rt0->GetDesc(&rd);
		const bool bb = is_back_buffer(rt0);

		// A new "segment" starts when the target or the kind of drawing changes: snapshot the target as it
		// was right before this draw, so consecutive snapshots show what each segment added.
		const uint64_t segment = (static_cast<uint64_t>(reinterpret_cast<uintptr_t>(rt0)) << 8) |
			(rs[0] ? 1 : 0) | (rs[3] ? 2 : 0) | (post ? 4 : 0);
		std::string snap;
		if (segment != g_last_segment && g_snapshots < g_max_snapshots)
		{
			char name[64];
			sprintf_s(name, "snap_%05u_rt%d.bmp", g_draw_index, rt_id(rt0));
			const std::string status = snapshot_surface(dev, rt0, g_dump_dir + "\\" + name, 2);
			snap = status == "ok" ? name : status;
			++g_snapshots;
		}
		g_last_segment = segment;

		if (g_csv != nullptr)
			fprintf(g_csv, "%u,%s,%u,%08X,%08X,%d,%d,%u,%u,%u,%d,%d,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lX,%d,%lX,%lu,%lu,%lu,%lu,%lu,%s\n",
				g_draw_index, kind, count, lookup_hash(ps), lookup_hash(vs), rt_id(rt0), bb ? 1 : 0, rd.Width, rd.Height,
				static_cast<unsigned>(rd.Format), rt_id(rt1), ds != nullptr ? 1 : 0,
				rs[0], rs[1], rs[2], rs[3], rs[4], rs[5], rs[6], rs[7], rs[8], post ? 1 : 0, fvf,
				vp.X, vp.Y, vp.Width, vp.Height, scissor, snap.c_str());

		for (IUnknown *u : { static_cast<IUnknown *>(ps), static_cast<IUnknown *>(vs), static_cast<IUnknown *>(decl),
				static_cast<IUnknown *>(rt0), static_cast<IUnknown *>(rt1), static_cast<IUnknown *>(ds) })
			if (u != nullptr)
				u->Release();
	}

	// ---- Ultrawide: 2D UI as a centred 16:9 picture ----
	// Everything drawn into the back buffer after the composite is 2D UI (HUD, menus, text). On a back buffer wider
	// than 16:9 each of those draws gets its viewport (and scissor) mapped into the centred 16:9 area, x' = ox + x*k,
	// width' = width*k (k = 16/9*h/w): the UI renders natively at the closest 16:9 size (1920x1080 for 2560x1080),
	// unstretched and centred; the 3D scene keeps the full width.
	bool g_ultrawide = true;
	bool g_ui_phase = false;                 // the composite has been drawn this frame
	D3DVIEWPORT9 g_vp_set = {};              // the last viewport we set (re-map only when the game changed it)
	bool g_vp_valid = false;
	uint32_t g_ui_mapped = 0, g_ui_mapped_last = 0;
	bool g_ultrawide_logged = false;

	void map_ui_viewport(command_list *cmd_list)
	{
		if (!g_ultrawide || !g_ui_phase || g_runtime == nullptr || g_cur_rt0 != g_runtime->get_current_back_buffer().handle)
			return;
		uint32_t bw = 0, bh = 0;
		g_runtime->get_screenshot_width_and_height(&bw, &bh);
		if (bh == 0 || bw * 9 <= bh * 16 + 9)
			return;                                   // 16:9 or narrower
		IDirect3DDevice9 *dev = native(cmd_list);
		D3DVIEWPORT9 vp = {};
		if (FAILED(dev->GetViewport(&vp)))
			return;
		if (g_vp_valid && memcmp(&vp, &g_vp_set, sizeof vp) == 0)
			return;                                   // still ours
		const float w169 = bh * 16.0f / 9.0f, k = w169 / bw, ox = (bw - w169) * 0.5f;
		D3DVIEWPORT9 m = vp;
		m.X = static_cast<DWORD>(ox + vp.X * k + 0.5f);
		m.Width = static_cast<DWORD>(vp.Width * k + 0.5f);
		dev->SetViewport(&m);
		g_vp_set = m;
		g_vp_valid = true;
		DWORD scissor = FALSE;
		if (SUCCEEDED(dev->GetRenderState(D3DRS_SCISSORTESTENABLE, &scissor)) && scissor)
		{
			RECT r;
			if (SUCCEEDED(dev->GetScissorRect(&r)))
			{
				r.left = static_cast<LONG>(ox + r.left * k + 0.5f);
				r.right = static_cast<LONG>(ox + r.right * k + 0.5f);
				dev->SetScissorRect(&r);
			}
		}
		++g_ui_mapped;
		if (!g_ultrawide_logged)
		{
			g_ultrawide_logged = true;
			char msg[160];
			sprintf_s(msg, "ghwt_bgfx: ultrawide UI at 16:9: back buffer %ux%u, UI area x %.0f width %.0f", bw, bh, ox, w169);
			reshade::log::message(reshade::log::level::info, msg);
		}
	}

	void on_draw_common(command_list *cmd_list, const char *kind, uint32_t count)
	{
		map_ui_viewport(cmd_list);
		if (g_auto && !g_scrub && g_pending_inject && !g_injected_this_frame)
		{
			g_pending_inject = false;
			if (gate_open())
			{
				g_inject_at = static_cast<int>(g_draw_index);
				inject_effects(cmd_list);
			}
			else
			{
				// Menu frame: suppress ReShade's end-of-frame pass entirely.
				g_injected_this_frame = true;
				g_runtime->render_effects(cmd_list, resource_view {}, resource_view {});
			}
		}

		if (g_dump_active)
			dump_draw(cmd_list, kind, count);

		if (g_cur_ps == g_composite_ps && g_runtime != nullptr && g_cur_rt0 == g_runtime->get_current_back_buffer().handle)
		{
			g_composite_seen = true;
			g_pending_inject = true; // the composite itself must finish first
			g_ui_phase = true;       // from the next draw on: 2D UI
		}

		if (g_scrub && g_draw_index == g_scrub_n)
		{
			IDirect3DDevice9 *dev = native(cmd_list);
			IDirect3DPixelShader9 *ps = nullptr;
			IDirect3DVertexShader9 *vs = nullptr;
			dev->GetPixelShader(&ps);
			dev->GetVertexShader(&vs);
			g_scrub_ps = lookup_hash(ps);
			g_scrub_vs = lookup_hash(vs);
			if (ps != nullptr) ps->Release();
			if (vs != nullptr) vs->Release();
			inject_effects(cmd_list);
		}
		++g_draw_index;
	}

	// ---- events ----
	void on_init_pipeline(device *, pipeline_layout, uint32_t count, const pipeline_subobject *subobjects, pipeline handle)
	{
		std::lock_guard<std::mutex> lock(g_map_mutex);
		for (uint32_t i = 0; i < count; ++i)
		{
			const pipeline_subobject &so = subobjects[i];
			if ((so.type == pipeline_subobject_type::pixel_shader || so.type == pipeline_subobject_type::vertex_shader) && so.data != nullptr)
			{
				const auto *desc = static_cast<const shader_desc *>(so.data);
				g_shader_hash[handle.handle] = desc->code != nullptr ? fnv1a(desc->code, desc->code_size) : 0;
			}
			else if (so.type == pipeline_subobject_type::input_layout && so.data != nullptr)
			{
				const auto *elements = static_cast<const input_element *>(so.data);
				bool post = false;
				for (uint32_t e = 0; e < so.count; ++e)
					if (elements[e].semantic != nullptr && strcmp(elements[e].semantic, "POSITIONT") == 0)
						post = true;
				g_decl_post[handle.handle] = post;
			}
		}
	}

	void on_destroy_pipeline(device *, pipeline handle)
	{
		std::lock_guard<std::mutex> lock(g_map_mutex);
		g_shader_hash.erase(handle.handle);
		g_decl_post.erase(handle.handle);
	}

	bool on_draw(command_list *cmd_list, uint32_t vertex_count, uint32_t, uint32_t, uint32_t)
	{
		on_draw_common(cmd_list, "draw", vertex_count);
		return false;
	}

	bool on_draw_indexed(command_list *cmd_list, uint32_t index_count, uint32_t, uint32_t, int32_t, uint32_t)
	{
		on_draw_common(cmd_list, "drawidx", index_count);
		return false;
	}

	// Fires before ReShade renders its end-of-frame effects: the game's own final frame.
	void on_present(command_queue *queue, swapchain *, const rect *, const rect *, uint32_t, const rect *)
	{
		if (g_dump_active)
		{
			IDirect3DDevice9 *dev = reinterpret_cast<IDirect3DDevice9 *>(queue->get_device()->get_native());
			IDirect3DSurface9 *bb = nullptr;
			if (g_runtime != nullptr)
				bb = reinterpret_cast<IDirect3DSurface9 *>(g_runtime->get_current_back_buffer().handle);
			const std::string status = snapshot_surface(dev, bb, g_dump_dir + "\\final_game.bmp", 1);
			if (g_csv != nullptr)
				fprintf(g_csv, "# final_game.bmp: %s, draws=%u, injected_at=%d, composite_seen=%d\n",
					status.c_str(), g_draw_index, g_inject_at, g_composite_seen ? 1 : 0);
		}

		if (g_auto && !g_scrub && !g_injected_this_frame && g_runtime != nullptr)
		{
			command_list *cmd_list = queue->get_immediate_command_list();
			if (g_composite_seen && gate_open())
			{
				g_inject_at = static_cast<int>(g_draw_index); // composite was the last draw: nothing after it
				inject_effects(cmd_list);
			}
			else
			{
				// No scene this frame (menus, loading): a zero view renders nothing and also suppresses
				// ReShade's end-of-frame pass, while keeping timers and uniforms ticking.
				g_injected_this_frame = true;
				g_runtime->render_effects(cmd_list, resource_view {}, resource_view {});
			}
		}
	}

	void on_bind_pipeline(command_list *, pipeline_stage stages, pipeline handle)
	{
		if ((stages & pipeline_stage::pixel_shader) == pipeline_stage::pixel_shader)
		{
			g_cur_ps = handle.handle != 0 ? lookup_hash(reinterpret_cast<const void *>(static_cast<uintptr_t>(handle.handle))) : 0;
			if (contains(g_scene_ps, g_cur_ps))
				g_scene_seen = true;
			else if (contains(g_gameplay_ps, g_cur_ps))
				g_gameplay_seen = true;
		}
	}

	void on_bind_render_targets(command_list *, uint32_t count, const resource_view *rtvs, resource_view)
	{
		g_cur_rt0 = count != 0 ? rtvs[0].handle : 0;
	}

	// Fires after ReShade's effects (end of frame or our injection): frame boundary.
	void on_reshade_present(effect_runtime *runtime)
	{
		if (g_dump_active)
		{
			uint32_t w = 0, h = 0;
			runtime->get_screenshot_width_and_height(&w, &h);
			std::vector<uint8_t> rgba(static_cast<size_t>(w) * h * 4);
			if (w != 0 && runtime->capture_screenshot(rgba.data()))
			{
				std::vector<uint8_t> bgr(static_cast<size_t>(w) * h * 3);
				for (size_t i = 0, n = static_cast<size_t>(w) * h; i < n; ++i)
				{
					bgr[i * 3 + 0] = rgba[i * 4 + 2];
					bgr[i * 3 + 1] = rgba[i * 4 + 1];
					bgr[i * 3 + 2] = rgba[i * 4 + 0];
				}
				write_bmp(g_dump_dir + "\\final_shown.bmp", w, h, bgr);
			}
			if (g_csv != nullptr)
			{
				fclose(g_csv);
				g_csv = nullptr;
			}
			g_dump_active = false;
			g_last_dump = g_dump_dir;
			reshade::log::message(reshade::log::level::info, ("ghwt_bgfx: dump complete, " + std::to_string(g_draw_index) + " draws").c_str());
		}

		g_draws_last_frame = g_draw_index;
		g_draw_index = 0;
		g_ui_phase = false;
		g_vp_valid = false;
		g_ui_mapped_last = g_ui_mapped;
		g_ui_mapped = 0;
		g_injected_this_frame = false;
		g_composite_seen = false;
		g_pending_inject = false;
		g_inject_at_last = g_inject_at;
		g_inject_at = -1;
		g_gate_open_last = gate_open();
		if (g_gameplay_seen)
			g_gameplay_hold = g_gameplay_hold_frames;
		else if (g_gameplay_hold != 0)
			--g_gameplay_hold;
		g_scene_seen = false;
		g_gameplay_seen = false;

		if (g_key_dump != 0 && runtime->is_key_pressed(g_key_dump))
			g_dump_armed = true;
		// Headless trigger for tooling: create <game>\ghwt_bgfx_dump.trigger to dump the next frame.
		static uint32_t frame_counter = 0;
		if (g_debug && ++frame_counter % 30 == 0)
		{
			static const std::string trigger = game_dir() + "\\ghwt_bgfx_dump.trigger";
			if (GetFileAttributesA(trigger.c_str()) != INVALID_FILE_ATTRIBUTES && DeleteFileA(trigger.c_str()))
				g_dump_armed = true;
		}
		if (g_key_scrub != 0 && runtime->is_key_pressed(g_key_scrub))
			g_scrub = !g_scrub;
		if (g_scrub)
		{
			const uint32_t step = runtime->is_key_down(VK_SHIFT) ? 25 : 1;
			if (runtime->is_key_pressed(VK_PRIOR))
				g_scrub_n += step;
			if (runtime->is_key_pressed(VK_NEXT))
				g_scrub_n = g_scrub_n > step ? g_scrub_n - step : 0;
		}

		if (g_dump_armed)
		{
			g_dump_armed = false;
			begin_dump(); // captures the next frame, start to finish
		}
	}

	// Reads a comma-separated list of hex shader hashes (e.g. "E5555C99,850F299B"), keeping the default if absent.
	void read_hash_list(effect_runtime *runtime, const char *key, std::vector<uint32_t> &out)
	{
		char buf[512] = {};
		size_t size = sizeof(buf);
		if (!reshade::get_config_value(runtime, "GHWT_BGFX", key, buf, &size))
			return;
		out.clear();
		for (char *ctx = nullptr, *tok = strtok_s(buf, ", ", &ctx); tok != nullptr; tok = strtok_s(nullptr, ", ", &ctx))
			out.push_back(static_cast<uint32_t>(strtoul(tok, nullptr, 16)));
	}

	void on_init_effect_runtime(effect_runtime *runtime)
	{
		g_runtime = runtime;
		reshade::get_config_value(runtime, "GHWT_BGFX", "Debug", g_debug);
		if (g_debug)
		{
			g_key_dump = VK_F10;
			g_key_scrub = VK_F9;
		}
		reshade::get_config_value(runtime, "GHWT_BGFX", "DumpKey", g_key_dump);
		reshade::get_config_value(runtime, "GHWT_BGFX", "ScrubKey", g_key_scrub);
		reshade::get_config_value(runtime, "GHWT_BGFX", "MaxSnapshots", g_max_snapshots);
		reshade::get_config_value(runtime, "GHWT_BGFX", "Auto", g_auto);
		char hex[16] = {};
		size_t hex_size = sizeof(hex);
		if (reshade::get_config_value(runtime, "GHWT_BGFX", "CompositePS", hex, &hex_size))
			g_composite_ps = static_cast<uint32_t>(strtoul(hex, nullptr, 16));
		reshade::get_config_value(runtime, "GHWT_BGFX", "Gate", g_gate);
		reshade::get_config_value(runtime, "GHWT_BGFX", "GameplayHoldFrames", g_gameplay_hold_frames);
		read_hash_list(runtime, "ScenePS", g_scene_ps);
		read_hash_list(runtime, "GameplayPS", g_gameplay_ps);
	}

	void on_destroy_effect_runtime(effect_runtime *runtime)
	{
		if (g_runtime == runtime)
			g_runtime = nullptr;
		if (g_csv != nullptr)
		{
			fclose(g_csv);
			g_csv = nullptr;
		}
		g_dump_active = false;
	}

	void draw_overlay(effect_runtime *)
	{
		ImGui::Text("Draws last frame: %u", g_draws_last_frame);
		ImGui::Checkbox("Ultrawide: UI as centred 16:9", &g_ultrawide);
		ImGui::Text("UI viewports mapped last frame: %u", g_ui_mapped_last);
		ImGui::Separator();
		ImGui::Checkbox("Auto: effects after scene composite only (experimental)", &g_auto);
		ImGui::Text("Composite PS %08X, effects applied before draw %d (-1 = none)", g_composite_ps, g_inject_at_last);
		ImGui::Checkbox("Gate: songs and cutscenes only", &g_gate);
		ImGui::Text("Gate %s (venue scene or highway in the last %u frames)", g_gate_open_last ? "OPEN" : "closed", g_gameplay_hold_frames);
		if (!g_debug)
			return;
		ImGui::Separator();
		if (ImGui::Button("Dump next frame (F10)"))
			g_dump_armed = true;
		if (!g_last_dump.empty())
			ImGui::TextWrapped("Last dump: %s", g_last_dump.c_str());
		ImGui::Separator();
		ImGui::Checkbox("Scrub: render effects before draw N (F9)", &g_scrub);
		int n = static_cast<int>(g_scrub_n);
		if (ImGui::DragInt("N (PgUp/PgDn, Shift x25)", &n, 1.0f, 0, 100000))
			g_scrub_n = n < 0 ? 0 : static_cast<uint32_t>(n);
		ImGui::Text("At N: PS %08X  VS %08X", g_scrub_ps, g_scrub_vs);
		if (g_scrub && g_scrub_n >= g_draws_last_frame)
			ImGui::TextUnformatted("N is past the last draw: effects run at end of frame.");
	}
}

BOOL APIENTRY DllMain(HMODULE module, DWORD reason, LPVOID)
{
	switch (reason)
	{
	case DLL_PROCESS_ATTACH:
		if (!reshade::register_addon(module))
			return FALSE;
		reshade::register_event<reshade::addon_event::init_pipeline>(on_init_pipeline);
		reshade::register_event<reshade::addon_event::destroy_pipeline>(on_destroy_pipeline);
		reshade::register_event<reshade::addon_event::draw>(on_draw);
		reshade::register_event<reshade::addon_event::draw_indexed>(on_draw_indexed);
		reshade::register_event<reshade::addon_event::present>(on_present);
		reshade::register_event<reshade::addon_event::bind_pipeline>(on_bind_pipeline);
		reshade::register_event<reshade::addon_event::bind_render_targets_and_depth_stencil>(on_bind_render_targets);
		reshade::register_event<reshade::addon_event::reshade_present>(on_reshade_present);
		reshade::register_event<reshade::addon_event::init_effect_runtime>(on_init_effect_runtime);
		reshade::register_event<reshade::addon_event::destroy_effect_runtime>(on_destroy_effect_runtime);
		reshade::register_overlay("Background-only shaders", draw_overlay);
		break;
	case DLL_PROCESS_DETACH:
		reshade::unregister_addon(module);
		break;
	}
	return TRUE;
}

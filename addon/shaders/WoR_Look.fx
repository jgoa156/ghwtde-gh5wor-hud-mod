// WoR_Look.fx: finishing pass for the Warriors of Rock look (part of the GHWT BGFX mod).
//
// Reference: Xbox 360 Warriors of Rock gameplay has crisp, gritty background detail, deep blacks and a slight
// corner falloff. This pass adds contrast-adaptive sharpening (CAS-style: strong on flat detail, weak on
// already-contrasty edges, so no halos) and an aspect-corrected vignette. The GHWT BGFX add-on runs the preset
// before the HUD is drawn, so both effects only touch the background.

#include "ReShade.fxh"

uniform float Sharpness <
	ui_type = "slider"; ui_min = 0.0; ui_max = 1.0;
	ui_label = "Sharpness";
	ui_tooltip = "Contrast-adaptive sharpening. 0 = off.";
> = 0.6;

uniform float VignetteAmount <
	ui_type = "slider"; ui_min = 0.0; ui_max = 1.0;
	ui_label = "Vignette amount";
> = 0.25;

uniform float VignetteStart <
	ui_type = "slider"; ui_min = 0.0; ui_max = 1.0;
	ui_label = "Vignette start";
	ui_tooltip = "Distance from the centre (0 = centre, 1 = corner) where the darkening begins.";
> = 0.55;

float3 Fetch(float2 uv, float2 offset)
{
	return tex2Dlod(ReShade::BackBuffer, float4(uv + offset * ReShade::PixelSize, 0.0, 0.0)).rgb;
}

float3 PS_WoRLook(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
	float3 c = Fetch(uv, float2(0.0, 0.0));
	float3 n = Fetch(uv, float2(0.0, -1.0));
	float3 s = Fetch(uv, float2(0.0, 1.0));
	float3 w = Fetch(uv, float2(-1.0, 0.0));
	float3 e = Fetch(uv, float2(1.0, 0.0));

	// Contrast-adaptive sharpening: the weight shrinks where local contrast is already high.
	float3 mn = min(c, min(min(n, s), min(w, e)));
	float3 mx = max(c, max(max(n, s), max(w, e)));
	float3 amp = sqrt(saturate(min(mn, 1.0 - mx) / max(mx, 1e-5)));
	float peak = -1.0 / lerp(8.0, 5.0, Sharpness);
	float3 wgt = amp * peak * (Sharpness > 0.0 ? 1.0 : 0.0);
	float3 color = saturate((c + (n + s + w + e) * wgt) / (1.0 + 4.0 * wgt));

	// Vignette, normalised to a 16:9 frame so ultrawide sides are not over-darkened.
	float2 q = uv - 0.5;
	q.x *= min(ReShade::AspectRatio, 16.0 / 9.0) / ReShade::AspectRatio * (16.0 / 9.0);
	float r = length(q) / length(float2(0.5 * 16.0 / 9.0, 0.5));
	color *= 1.0 - VignetteAmount * smoothstep(VignetteStart, 1.0, r);

	return color;
}

technique WoR_Look <
	ui_tooltip = "Warriors of Rock finishing pass: adaptive sharpening + vignette (background only with GHWT BGFX).";
>
{
	pass
	{
		VertexShader = PostProcessVS;
		PixelShader = PS_WoRLook;
	}
}

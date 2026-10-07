// GH5_Grade.fx: tone grade toward Guitar Hero 5's look (part of the GHWT BGFX mod).
//
// Measured on matched gameplay of the same song (GH5 original vs GHWT:DE + GHWoR preset, 2026-10-04): GH5's
// background has much deeper shadows (luma p10 0.022 vs 0.063, p50 0.143 vs 0.197) with the same highlights.
// This pass is a soft toe on luma, y' = y*y/(y+Toe)*(1+Toe), which pulls shadows and low mids down and leaves
// highlights almost untouched; chroma is scaled with luma so colours keep their hue. Toe 0.10 at strength 1.0
// reproduces GH5's luma percentiles within ~0.01 up to p75. Runs before the HUD (background only with GHWT BGFX).

#include "ReShade.fxh"

uniform float Toe <
	ui_type = "slider"; ui_min = 0.0; ui_max = 0.5;
	ui_label = "Toe";
	ui_tooltip = "How hard the shadows are pulled down. 0.12 is the shipped default.";
> = 0.12;

uniform float Strength <
	ui_type = "slider"; ui_min = 0.0; ui_max = 1.0;
	ui_label = "Strength";
	ui_tooltip = "Blend between the original image (0) and the full grade (1).";
> = 1.0;

float3 PS_GH5Grade(float4 pos : SV_Position, float2 uv : TEXCOORD) : SV_Target
{
	float3 c = tex2D(ReShade::BackBuffer, uv).rgb;
	float y = dot(c, float3(0.2126, 0.7152, 0.0722));
	float yt = y * y / (y + Toe + 1e-6) * (1.0 + Toe);
	float3 graded = c * (yt / max(y, 1e-5));
	return saturate(lerp(c, graded, Strength));
}

technique GH5_Grade <
	ui_tooltip = "Guitar Hero 5 tone: deeper shadows, same highlights (background only with GHWT BGFX).";
>
{
	pass
	{
		VertexShader = PostProcessVS;
		PixelShader = PS_GH5Grade;
	}
}

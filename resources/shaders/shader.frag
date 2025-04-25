#version 330

uniform sampler2D surface;
uniform sampler2D ui_surf;
uniform sampler2D bg_surf;

uniform float time;

out vec4 f_color;
in vec2 uv;


void main() {
    vec2 tex_uv = uv;

    // BG
    vec4 tex;
    tex.r = texture(bg_surf, tex_uv).r;
    tex.g = texture(bg_surf, tex_uv).g;
    tex.b = texture(bg_surf, tex_uv).b;
    tex.a = 1.0;
    
    // SURFACE
    vec4 src_color = texture(surface, tex_uv);
    //UI
    vec4 ui_color = texture(ui_surf, tex_uv);
    
    // Blend textures
    if (src_color.a > 0.5) {
        tex = mix(tex, src_color, 0.6);
    }
    
    // Add UI elements
    if (ui_color.r > 0.0) {
        tex += ui_color;
    }

    // Final color output
    f_color = tex;
}
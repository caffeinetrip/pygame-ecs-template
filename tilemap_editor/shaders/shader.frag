#version 330

uniform sampler2D surface;
uniform sampler2D ui_surf;
uniform sampler2D light_surf;
uniform sampler2D game_surf;
uniform float time;

uniform bool overlay = false;
uniform float scanlines_opacity = 0.4;
uniform float scanlines_width = 0.25;
uniform float grille_opacity = 0.3;
uniform vec2 resolution = vec2(640.0, 480.0);
uniform bool pixelate = true;
uniform bool roll = true;
uniform float roll_speed = 8.0;
uniform float roll_size = 15.0;
uniform float roll_variation = 1.8;
uniform float distort_intensity = 0.05;
uniform float noise_opacity = 0.4;
uniform float noise_speed = 5.0;
uniform float static_noise_intensity = 0.06;
uniform float aberration = 0.03;
uniform float brightness = 1.4;
uniform bool discolor = true;
uniform float warp_amount = 1.0;
uniform bool clip_warp = false;
uniform float vignette_intensity = 0.4;
uniform float vignette_opacity = 0.5;

out vec4 f_color;
in vec2 uv;

const vec3 color_ramp[4] = vec3[4](
    vec3(40 / 255.0, 35 / 255.0, 40 / 255.0),
    vec3(84 / 255.0, 92 / 255.0, 126 / 255.0),
    vec3(197 / 255.0, 105 / 255.0, 129 / 255.0),
    vec3(163 / 255.0, 162 / 255.0, 154 / 255.0)
);

vec2 random(vec2 uv) {
    uv = vec2(dot(uv, vec2(127.1,311.7)),
              dot(uv, vec2(269.5,183.3)));
    return -1.0 + 2.0 * fract(sin(uv) * 43758.5453123);
}

float noise(vec2 uv) {
    vec2 uv_index = floor(uv);
    vec2 uv_fract = fract(uv);
    vec2 blur = smoothstep(0.0, 1.0, uv_fract);

    return mix(mix(dot(random(uv_index + vec2(0.0,0.0)), uv_fract - vec2(0.0,0.0)),
                  dot(random(uv_index + vec2(1.0,0.0)), uv_fract - vec2(1.0,0.0)), blur.x),
              mix(dot(random(uv_index + vec2(0.0,1.0)), uv_fract - vec2(0.0,1.0)),
                  dot(random(uv_index + vec2(1.0,1.0)), uv_fract - vec2(1.0,1.0)), blur.x), blur.y) * 0.5 + 0.5;
}

vec2 warp(vec2 uv) {
    vec2 delta = uv - 0.5;
    float delta2 = dot(delta.xy, delta.xy);
    float delta4 = delta2 * delta2;
    float delta_offset = delta4 * warp_amount;
    return uv + delta * delta_offset;
}

float border(vec2 uv) {
    float radius = min(warp_amount, 0.08);
    radius = max(min(min(abs(radius * 2.0), abs(1.0)), abs(1.0)), 1e-5);
    vec2 abs_uv = abs(uv * 2.0 - 1.0) - vec2(1.0, 1.0) + radius;
    float dist = length(max(vec2(0.0), abs_uv)) / radius;
    float square = smoothstep(0.96, 1.0, dist);
    return clamp(1.0 - square, 0.0, 1.0);
}

float vignette(vec2 uv) {
    uv *= 1.0 - uv.xy;
    float vignette = uv.x * uv.y * 15.0;
    return pow(vignette, vignette_intensity * vignette_opacity);
}

void main() {
    vec4 base_color = texture(game_surf, uv);
    
    vec4 src_color = texture(surface, uv);
    if (src_color.a > 0.5) {
        int color_i = 0;
        for (int i = 0; i < 4; i++) {
            if (length(color_ramp[i] - src_color.rgb) < (5.0 / 255.0)) {
                color_i = i;
            }
        }
        color_i = max(0, color_i);
        base_color = vec4(color_ramp[color_i], 1.0);
    }

    vec4 ui_color = texture(ui_surf, uv);
    if (ui_color.r > 0.0) {
        base_color += ui_color;
    }

    vec2 tex_uv = uv;

    if (pixelate) {
        tex_uv = floor(tex_uv * resolution + 0.5) / resolution;
    }
    
    float roll_line = 0.0;
    if (roll || noise_opacity > 0.0) {
        roll_line = smoothstep(0.3, 0.9, sin(tex_uv.y * roll_size - (time * roll_speed)));
        roll_line *= roll_line * smoothstep(0.3, 0.9, sin(tex_uv.y * roll_size * roll_variation - (time * roll_speed * roll_variation)));
    }
    
    vec2 roll_uv = vec2((roll_line * distort_intensity * (1.0 - tex_uv.x)), 0.0);
    
    vec4 tex;
    if (roll) {
        tex.r = texture(game_surf, tex_uv + roll_uv * 0.8 + vec2(aberration, 0.0) * 0.1).r;
        tex.g = texture(game_surf, tex_uv + roll_uv * 1.2 - vec2(aberration, 0.0) * 0.1).g;
        tex.b = texture(game_surf, tex_uv + roll_uv).b;
        tex.a = 1.0;
    } else {
        tex.r = texture(game_surf, tex_uv + vec2(aberration, 0.0) * 0.1).r;
        tex.g = texture(game_surf, tex_uv - vec2(aberration, 0.0) * 0.1).g;
        tex.b = texture(game_surf, tex_uv).b;
        tex.a = 1.0;
    }
    
    tex = mix(tex, base_color, 0.5);
    
    if (grille_opacity > 0.0) {
        float g_r = smoothstep(0.85, 0.95, abs(sin(tex_uv.x * (resolution.x * 3.14159265))));
        tex.r = mix(tex.r, tex.r * g_r, grille_opacity);
        
        float g_g = smoothstep(0.85, 0.95, abs(sin(1.05 + tex_uv.x * (resolution.x * 3.14159265))));
        tex.g = mix(tex.g, tex.g * g_g, grille_opacity);
        
        float b_b = smoothstep(0.85, 0.95, abs(sin(2.1 + tex_uv.x * (resolution.x * 3.14159265))));
        tex.b = mix(tex.b, tex.b * b_b, grille_opacity);
    }
    
    tex.rgb = clamp(tex.rgb * brightness, 0.0, 1.0);
    
    if (scanlines_opacity > 0.0) {
        float scanlines = smoothstep(scanlines_width, scanlines_width + 0.5, abs(sin(tex_uv.y * (resolution.y * 3.14159265))));
        tex.rgb = mix(tex.rgb, tex.rgb * vec3(scanlines), scanlines_opacity);
    }
    
    tex.rgb *= vignette(tex_uv);

    f_color = tex;
}
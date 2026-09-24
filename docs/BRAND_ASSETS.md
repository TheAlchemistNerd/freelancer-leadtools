# OSFreelance brand assets

These assets implement the **Independent Workbench** direction in
docs/internal/osfreelance-web-design.md. They are deliberately simple,
editable, and dependency-free: vector masters are SVG and the raster outputs
are generated locally from the same geometry and brand colors.

## Asset inventory

- osfreelance-mark.svg: standalone product mark.
- osfreelance-logo.svg: horizontal wordmark for light surfaces.
- favicon.svg: scalable browser icon.
- favicon.ico and favicon-32.png: legacy and PNG browser fallbacks.
- apple-touch-icon.png: 180x180 home-screen icon.
- social-card.svg: editable 1200x630 social-card master.
- social-card.png: production Open Graph and social-sharing image.
- site.webmanifest: browser application metadata.

The palette is warm canvas #F6F4EF, ink #172B2A, teal #145C50, ochre
#E8B85C, muted ink #526361, and border #D8DEDA.

## Regeneration

From the repository root, run:

    .\scripts\generate_brand_assets.ps1

The script regenerates the PNG and ICO derivatives. SVG masters remain the
source for vector usage and should be edited deliberately. Keep the social
card at 1200x630, keep important text away from its edges, and preserve an
absolute HTTPS WEB_PUBLIC_ORIGIN in production so link previews can retrieve
the image.

These assets are original project artwork. Do not substitute fabricated
customer logos, endorsement badges, stock photography, or unverified claims.

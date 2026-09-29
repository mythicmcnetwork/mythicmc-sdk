# README logo

The logo is served by the shared MythicMC CDN:

https://cdn.mythicmc.net/sdk/logo.png

Place the PNG at `branding/public/logo.png` (Git-ignored), then run from the
`apps-cdn` checkout:

```sh
npm run sync:assets -- /path/to/mythicmc-sdk/branding/public sdk --dry-run
npm run sync:assets -- /path/to/mythicmc-sdk/branding/public sdk
```

Only assets are uploaded. Do not deploy a separate Worker for this repository.
`_headers` is skipped; the upload command sets content type and cache metadata.
When replacing the logo, change the README's `?v=` value to invalidate downstream
image caches. Keep the old Worker until the CDN URL and README have been verified.

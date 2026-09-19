# README logo

The PNG is hosted on Cloudflare, outside GitHub:

https://mythicmc-sdk-assets.acc500833.workers.dev/logo.png

To update it, place the PNG at `branding/public/logo.png`, then run from the repository root:

```sh
npx wrangler deploy --config branding/wrangler.jsonc
```

The PNG is Git-ignored. Only the hosting configuration and cache headers are committed. This Worker serves the logo independently of the API and developer portal.

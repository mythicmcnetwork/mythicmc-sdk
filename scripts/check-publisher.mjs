// Exchange GitHub's identity for a short-lived registry token without publishing.
// Tokens stay in memory and are never printed or saved as workflow outputs.
const registry = process.argv[2]
if (!['npm', 'pypi'].includes(registry)) throw new Error('Choose npm or pypi')
const requestUrl = process.env.ACTIONS_ID_TOKEN_REQUEST_URL
const requestToken = process.env.ACTIONS_ID_TOKEN_REQUEST_TOKEN
if (!requestUrl || !requestToken) throw new Error('Run in GitHub Actions with id-token: write')
async function json(url, options) {
  const response = await fetch(url, { ...options, signal: AbortSignal.timeout(30000) })
  if (!response.ok) throw new Error(`${new URL(url).hostname} rejected authentication: HTTP ${response.status}. Check owner, repository, release.yml and environment release in trusted publishing settings.`)
  return response.json()
}
const url = new URL(requestUrl)
url.searchParams.set('audience', registry === 'npm' ? 'npm:registry.npmjs.org' : 'pypi')
const identity = await json(url, { headers: { Authorization: `Bearer ${requestToken}` } })
if (!identity.value) throw new Error('GitHub returned no identity token')
const exchange = registry === 'npm'
  ? await json('https://registry.npmjs.org/-/npm/v1/oidc/token/exchange/package/@mythicmcnetwork%2ftypescript-sdk', { method: 'POST', headers: { Authorization: `Bearer ${identity.value}` } })
  : await json('https://pypi.org/_/oidc/mint-token', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token: identity.value }) })
if (!exchange.token) throw new Error(`${registry} returned no publishing token`)
console.log(`${registry}: trusted publisher authentication passed; no package uploaded.`)

#!/usr/bin/env bash
# Push this repo to GitHub with a fine-grained PAT, without leaving the token on disk
# or in your shell history.
#
#   1) create the fine-grained token (see README -> "Push to GitHub")
#   2) export it for this shell only:
#        read -rsp "GitHub token: " GH_TOKEN && export GH_TOKEN && echo
#   3) run:
#        ./tools/deploy.sh <your-github-username> <repo-name>
#
# The token is fed to git through a credential helper for one invocation only.
set -euo pipefail

USER_="${1:?usage: deploy.sh <github-username> <repo-name>}"
REPO="${2:?usage: deploy.sh <github-username> <repo-name>}"
: "${GH_TOKEN:?set GH_TOKEN first (read -rsp \"GitHub token: \" GH_TOKEN)}"

cd "$(dirname "$0")/.."

# create the repo if it doesn't exist yet (201 = created, 422 = already exists)
body=$(curl -s -w '\n%{http_code}' -X POST https://api.github.com/user/repos \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -d "{\"name\":\"$REPO\",\"private\":false,\"description\":\"pixelspark restaurant landing page\"}")
code=$(printf '%s' "$body" | tail -n1)
case "$code" in
  201) echo "created https://github.com/$USER_/$REPO" ;;
  422) echo "repo already exists — pushing into it" ;;
  403) echo "ERROR: token lacks 'Administration: Read and write', so it cannot create repos." >&2
       echo "       Either add that permission, or create an empty repo in the browser and re-run." >&2
       exit 1 ;;
  *)   echo "ERROR: create-repo returned HTTP $code" >&2
       printf '%s\n' "$body" | head -n -1 >&2
       exit 1 ;;
esac

git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$USER_/$REPO.git"

# one-shot credential injection: -c credential.helper=<inline>, never written to .git/config
git -c credential.helper='!f() { echo username=x-access-token; echo password=$GH_TOKEN; }; f' \
    push -u origin "$(git branch --show-current)"

unset GH_TOKEN
echo "done -> https://github.com/$USER_/$REPO"

# Push to GitHub

The repo is already initialised and committed (`main`, 1 commit, ~9 MB). All that's left is
a token and one command.

---

## 1. Create the fine-grained token

Fine-grained PATs are the safest option: you scope them to **one repository** and grant only
the permissions needed.

1. Sign in, then open **<https://github.com/settings/personal-access-tokens/new>**
   (also reachable via *Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token*).
2. **Token name** — something recognisable, e.g. `pixelspark-deploy`.
3. **Expiration** — 7 days is plenty for a one-off push. Shorter is better.
4. **Resource owner** — your account (or the org, if you push to an org repo).
5. **Repository access** → *Only select repositories* → pick the repo.
   - If the repo **doesn't exist yet**, choose *All repositories* for now (or create the empty
     repo first, then come back and select it).
6. **Permissions** → expand **Repository permissions** and set:

   | Permission | Access | Why |
   |---|---|---|
   | **Contents** | **Read and write** | required to push commits |
   | Metadata | Read-only | auto-selected, mandatory |
   | Workflows | Read and write | *only* if you plan to commit `.github/workflows/*` |

   Leave everything else at **No access**.
7. **Generate token**, then copy it immediately — it starts with `github_pat_…` and is
   **shown only once**.

> If you'd rather create the repo from the command line, also grant
> **Administration → Read and write** (needed for the "create repo" API call in `deploy.sh`).
> Otherwise create an **empty** repo in the browser (no README, no .gitignore, no licence)
> and skip that step.

---

## 2. Push

The token must never end up in `.git/config`, a file, or your shell history. This keeps it in
memory only:

```bash
cd ~/                       # this workspace
read -rsp "GitHub token: " GH_TOKEN && export GH_TOKEN && echo
./tools/deploy.sh <your-username> <repo-name>
```

`deploy.sh` does three things:

- creates the repo over the API if it doesn't exist (needs *Administration* permission),
- points `origin` at it,
- pushes using a **one-shot credential helper**, so nothing is written to disk.

Then it prints the repo URL.

### Manual equivalent

If you prefer typing it out:

```bash
read -rsp "GitHub token: " GH_TOKEN && export GH_TOKEN && echo

git remote set-url origin https://github.com/<user>/<repo>.git
git -c credential.helper='!f() { echo username=x-access-token; echo password=$GH_TOKEN; }; f' \
    push -u origin main

unset GH_TOKEN
```

Note the username is literally **`x-access-token`** for a fine-grained token
(`git` also works). For a *classic* token the username is your GitHub username.

---

## 3. Never paste the token into chat

A token pasted into a conversation is compromised — treat it as burned and revoke it
(*Settings → Developer settings → Personal access tokens*). Everything above is designed so
you never need to share it with me.

If you hit trouble, paste the **error message only** (it never contains the token) and I'll
tell you which permission is missing.

---

## Common errors → what they mean

| Message | Fix |
|---|---|
| `remote: Permission to <repo> denied to x-access-token` | token lacks **Contents: Read and write**, or the repo isn't in the token's *Repository access* list |
| `Repository not found` | the repo doesn't exist yet → create it empty, or grant **Administration: Read and write** |
| `Support for password authentication was removed` | you pasted the token as a password for the wrong URL, or `GH_TOKEN` was empty |
| `refusing to allow a Personal Access Token to create or update workflow` | add **Workflows: Read and write** |
| `Updates were rejected because the remote contains work…` | the repo was created with a README; run `git pull --rebase origin main` then push again |

---

## Publishing the page (optional)

`index.html` is fully self-contained, so **GitHub Pages** works with no build step:

1. Repo → *Settings → Pages*
2. **Source**: *Deploy from a branch* → **Branch: `main`**, folder **`/ (root)`**
3. Save — the site appears at `https://<user>.github.io/<repo>/` in about a minute.

A workflow file for Pages (if you prefer Actions) needs the **Workflows** permission on the
token, which is why it's listed as optional above.

# Making it look like yours

Everything visual lives in one file: `static/style.css`. You don't need to
touch `app.py` or the `templates/` folder to change how the site looks —
just that one file. Here's how to find your way around it.

## 1. Colors — the fastest way to change the whole feel

At the very top of `style.css` you'll see:

```css
:root {
  --paper: #EEF0EA;        /* page background */
  --paper-raised: #F7F8F3; /* cards, input fields */
  --ink: #21262B;          /* main text */
  --ink-soft: #565D62;     /* secondary text (dates, captions) */
  --accent: #2F6F5E;       /* links, buttons, highlights */
  --accent-soft: #DCE8E3;  /* pale wash used behind the cover photo */
  --rule: #D3D4C6;         /* thin divider lines */
  --danger: #A6432E;       /* delete buttons, error text */
}
```

Change any of these hex codes and the whole site updates everywhere,
because every other style references these variables instead of writing
colors directly. Try picking a palette around one photo or mood you like —
for example, pull 3-4 colors from a favorite photo using a tool like
https://coolors.co, and drop them in here.

Some starting points to try:
- **Warm and cozy:** `--paper: #F7F1E8; --accent: #B5542C;`
- **Cool and minimal:** `--paper: #F5F6F8; --accent: #3556D4;`
- **Moody/dark:** `--paper: #17181B; --paper-raised: #202226; --ink: #EDEDED; --accent: #E8A33D;`
  (dark mode needs a bit more care — you'll also want to check text stays
  readable on `--paper-raised`)

## 2. Fonts

Near the top of `templates/base.html` there's a line loading Google Fonts:

```html
<link href="https://fonts.googleapis.com/css2?family=Fraunces:...&family=Literata:...&family=IBM+Plex+Mono:..." rel="stylesheet">
```

Swap in any fonts from https://fonts.google.com — pick one, click "Get font",
copy the `<link>` snippet it gives you, and replace the line above with it.
Then update these three variables in `style.css` to match the font names
you chose:

```css
--font-display: "Fraunces", serif;   /* headlines, titles */
--font-body: "Literata", serif;      /* paragraph text */
--font-mono: "IBM Plex Mono", monospace; /* dates, labels, buttons */
```

## 3. Layout

- `.page { max-width: 720px; }` — controls how wide the whole site is.
  Bump it to `900px` or more for a wider layout.
- `.profile-cover { height: 200px; }` — cover photo banner height.
- `.profile-avatar { width: 112px; height: 112px; }` — profile photo size.
- `.post-list-item` — controls spacing between posts on the homepage.

## 4. See your changes instantly

While `python app.py` is running, just edit `style.css`, save the file, and
refresh your browser — no restart needed. This makes it easy to try a lot
of small changes quickly.

## 5. If you want more structural changes

The actual page structure (what shows where) lives in the `.html` files in
`templates/`. For example, to move the "Edit profile" button above your
name instead of beside it, you'd edit `templates/profile.html`. Each file
maps to one page:

| File | Page |
|---|---|
| `templates/base.html` | Shared header/footer on every page |
| `templates/index.html` | Homepage (post list) |
| `templates/post.html` | Individual blog post |
| `templates/profile.html` | Public profile |
| `templates/dashboard.html` | Your private post list |
| `templates/edit_post.html` | Write/edit a post |
| `templates/edit_profile.html` | Edit your profile + photos |

These use Jinja templating — anything inside `{{ }}` is dynamic content
(like `{{ post.title }}`), and anything inside `{% %}` is logic (loops,
conditionals). You can rearrange the HTML around those freely without
breaking anything, as long as you don't delete the `{{ }}` / `{% %}` parts.

If you get stuck on a specific change, paste me the piece of `style.css` or
the template you're editing and tell me what you're going for — happy to
help you debug it rather than hand you a finished version.

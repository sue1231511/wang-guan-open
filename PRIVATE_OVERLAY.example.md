# Private overlay pattern

Keep private customizations outside the public repository.

Example private-only structure:

```text
private-overlay/
  persona.py
  context_private.py
  tools_private.py
  miniapp/
  secrets.env
```

At deployment time, copy or mount those files into the public gateway image.
Never commit the actual private overlay to the public repository.

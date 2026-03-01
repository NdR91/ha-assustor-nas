<!-- Context: standards/docs | Priority: critical | Version: 2.0 | Updated: 2025-01-21 -->

# Documentation Standards (Home Assistant Custom Integration)

## Quick Reference

**Golden Rule**: Prefer module docstrings over separate markdown files.

**Document** (✅ DO):
- WHY decisions were made (in `docs/development/DECISIONS.md`).
- Complex algorithms/logic.
- Public APIs, setup, common use cases.
- Breaking changes (in commit messages and documentation).

**Don't Document** (❌ DON'T):
- Obvious code (e.g., `i++` doesn't need a comment).
- What code does (should be self-explanatory).
- Random markdown files in code directories.
- Documentation in `.github/` unless it's a GitHub-specified file.

**Principles**: Audience-focused, Show don't tell, Keep current.

---

## Principles

**Audience-focused**: Write for users (what/how), developers (why/when), contributors (setup/conventions).
**Show, don't tell**: Code examples, real use cases, expected output.
**Keep current**: Update with code changes, remove outdated info, mark deprecations.

## Documentation Strategy

**Three types of content with clear separation:**

1. **Agent Instructions** - How AI should write code (`.github/instructions/`, `AGENTS.md`).
2. **Developer Documentation** - Architecture and design decisions (`docs/development/`).
3. **User Documentation** - End-user guides (`docs/user/`).

**AI Planning:** Use `.ai-scratch/` for temporary notes (never committed).

## Function Documentation

```python
def calculate_total(price: float, tax_rate: float) -> float:
    """Calculate total price including tax.

    Args:
        price: Base price.
        tax_rate: Tax rate (0-1).

    Returns:
        Total with tax.
    """
    return price * (1 + tax_rate)
```

## What to Document

### ✅ DO
- **WHY** decisions were made.
- Complex algorithms/logic.
- Non-obvious behavior.
- Public APIs.
- Setup/installation.
- Common use cases.
- Known limitations.
- Workarounds (with explanation).

### ❌ DON'T
- Obvious code.
- What code does.
- Redundant information.
- Outdated/incorrect info.

## Comments

### Good
```python
# Calculate discount by tier (Bronze: 5%, Silver: 10%, Gold: 15%)
discount = get_discount_by_tier(customer.tier)

# HACK: API returns null instead of [], normalize it
items = response.items or []

# TODO: Use async/await when Node 18+ is minimum
```

### Bad
```python
# Increment i
i += 1

# Get user
user = get_user()
```

## Translations

**Translation strategy:**
- Use placeholders in code (e.g., `"config.step.user.title"`) - functionality works without translations.
- Update `en.json` only when asked or at major feature completion.
- NEVER update other language files automatically - extremely time-consuming.
- Ask before updating multiple translation files.
- Priority: Business logic first, translations later.

## Best Practices

✅ Explain WHY, not just WHAT.
✅ Include working examples.
✅ Show expected output.
✅ Cover error handling.
✅ Use consistent terminology.
✅ Keep structure predictable.
✅ Update when code changes.

**Golden Rule**: If users ask the same question twice, document it.
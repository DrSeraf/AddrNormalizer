from ..clean.text_normalize import norm_text, is_garbage

def join_nonempty(parts, sep=", "):
    clean = [p for p in (norm_text(x) for x in parts) if p and not is_garbage(p)]
    return sep.join(clean)

def assemble_addr_norm(country, region, district, locality, street_norm, house_number, zip_norm):
    # street + house (в любой последовательности, пока: "street house")
    street_block = join_nonempty([f"{street_norm} {house_number}".strip()])
    # базовый универсальный шаблон
    return join_nonempty([
        street_block,
        locality,
        region,
        district,
        zip_norm,
        country,
    ])

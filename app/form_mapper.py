def map_to_form(entities, template):
    form = {}
    for k, v in template.items():
        form[v] = entities.get(k, "")
    return form

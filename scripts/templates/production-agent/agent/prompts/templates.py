INTENT_PROMPTS = {
    "general": "Process the general query: {query}",
    "crm_lookup": "Lookup customer details in CRM: {query}",
    "search": "Perform a secure web and repository code search: {query}"
}

def get_intent_prompt(intent: str, **kwargs) -> str:
    template = INTENT_PROMPTS.get(intent, INTENT_PROMPTS["general"])
    return template.format(**kwargs)

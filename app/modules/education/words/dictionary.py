import httpx


async def fetch_dictionary_data(word: str) -> dict:
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.get(url)
        res.raise_for_status()
        data = res.json()[0]

    meaning_block = data["meanings"][0]
    definition = meaning_block["definitions"][0]

    return {
        "pos": meaning_block["partOfSpeech"],
        "meaning": definition["definition"],
        "transcription": data["phonetics"][0].get("text"),
        "examples": [
            {"text": definition.get("example")}
        ] if definition.get("example") else [],
        "synonyms": definition.get("synonyms", []),
        "difficulty": "medium",
        "meta_data": {
            "source": "dictionaryapi.dev",
            "frequency": "unknown",
        }
    }

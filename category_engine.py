def get_category_engine(category):

    category = str(category).lower()

    if category == "crypto":
        return "crypto"

    if category == "sports":
        return "sports"

    if category == "weather":
        return "weather"

    if category == "politics":
        return "politics"

    if category == "entertainment":
        return "entertainment"

    return "general"
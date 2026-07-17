from googlenewsdecoder import new_decoderv1


def decode_google_news_url(url: str) -> str:
    result = new_decoderv1(url)
    if result.get("status"):
        return result["decoded_url"]

    return "Nie udało się zdekodować"

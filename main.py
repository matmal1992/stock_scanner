from app.providers.yahoo import download.
from app.scanners.momentum_scanner import MomentumScanner
from app.universe.gpw import GPW_TICKERS


def main():
    provider = YahooProvider()
    scanner = MomentumScanner(provider)

    ranking = scanner.scan(GPW_TICKERS)

    print(ranking.head(20))


if __name__ == "__main__":
    main()
 
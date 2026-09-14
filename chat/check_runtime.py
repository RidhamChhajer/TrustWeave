"""Check the revalidated runtime before starting the desktop demo."""
import ssl
import sys


def main():
    if sys.version_info < (3, 14) or ssl.OPENSSL_VERSION_INFO < (3, 0) or not ssl.HAS_TLSv1_3:
        print("Run setup-demo.cmd using Python 3.14 with OpenSSL 3.0 or newer and TLS 1.3 support.")
        return 1
    print(f"Python {sys.version.split()[0]}; {ssl.OPENSSL_VERSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

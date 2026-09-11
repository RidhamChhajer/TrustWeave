import asyncio

from verification.verification import Outcome, VerificationRequest, verify


def test_verification_outcomes_and_timeout():
    request = VerificationRequest.create("1" * 32, "a" * 64, "low_trust")
    async def run():
        for expected in Outcome:
            async def response(_request):
                return expected
            assert await verify(request, response) == expected
        async def stalled(_request):
            await asyncio.sleep(10)
        assert await verify(request, stalled, timeout=0.01) == Outcome.TIMEOUT
    asyncio.run(run())
    assert request.simulated and len(request.pair_fingerprint.replace(" ", "")) == 64

import asyncio
import uuid

from campuslink.identity.device import IdentityStore
from campuslink.identity.trust import TrustedPeer, TrustStore
from campuslink.network.protocol import MessageType, ProtocolMessage
from campuslink.network.secure_transport import PeerClient, PeerServer


def test_trusted_peers_exchange_authenticated_message(tmp_path):
    async def scenario():
        alice = IdentityStore(tmp_path / "alice").load_or_create("Alice")
        bob = IdentityStore(tmp_path / "bob").load_or_create("Bob")
        alice_trust = TrustStore(tmp_path / "alice-trust.json")
        bob_trust = TrustStore(tmp_path / "bob-trust.json")
        alice_trust.trust(TrustedPeer(bob.device_id, "Bob", bob.fingerprint))
        bob_trust.trust(TrustedPeer(alice.device_id, "Alice", alice.fingerprint))
        received = []

        async def handler(peer, message):
            received.append((peer, message))
            return {"status": "delivered"}

        server = PeerServer(bob, bob_trust, handler, host="127.0.0.1")
        port = await server.start()
        message = ProtocolMessage(MessageType.CHAT_MESSAGE, str(uuid.uuid4()), {"body": "Hi"})
        peer, response = await PeerClient(alice, alice_trust).request(
            "127.0.0.1", port, message
        )
        await server.close()
        assert peer.device_id == bob.device_id
        assert response.message_type is MessageType.CHAT_ACK
        assert response.payload["status"] == "delivered"
        assert received[0][1] == message

    asyncio.run(scenario())

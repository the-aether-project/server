const videoPlayer = document.querySelector("#player")
const startButton = document.querySelector("#start")
const closeButton = document.querySelector("#close")
closeButton.disabled = true;

const socket = new WebSocket(ws_url);

socket.onopen = () => {
    console.log(`WebSocket connection established to server-obtained url: ${ws_url}`);
}

socket.onmessage = async (event) => {
    const data = JSON.parse(event.data);
    switch (data.type) {
        case 'offer':
            handleOffer(data.stun_server, data.offer);
            break
        case 'msg':
            handleMsg(data.msg);
            break
    }
}

async function handleOffer(stun_server, offer) {
    let config = {
        sdpSemantics: 'unified-plan',
        iceServers: [{ urls: [stun_server] }]
    }

    const remoteOffer = new RTCSessionDescription(offer);
    const pc = new RTCPeerConnection(config);

    pc.addEventListener("track", (stream) => {
        if (stream.track.kind == "video") {
            videoPlayer.srcObject = stream.streams[0];
            videoPlayer.play().catch((err) => { console.log("Cannot player videplayer, ", err) })
        }

        closeButton.disabled = false;
    })

    await pc.setRemoteDescription(remoteOffer);
    await pc.setLocalDescription(await pc.createAnswer())
    socket.send(JSON.stringify({ type: "answer", payload: { sdp: pc.localDescription.sdp, type: pc.localDescription.type } }));
}

async function closeConnection() {
    socket.send(
        JSON.stringify({
            type: "closeConnection"
        })
    )

    videoPlayer.srcObject.getTracks().forEach(track => track.stop());
    videoPlayer.srcObject = null;
    closeButton.disabled = true;
}

function handleMsg(msg) {
    console.log(`Inbound message: ${msg}`);
}


function init() {
    if (!ws_url) {
        console.error("Could not obtain websocket endpoint from the server.");
        return
    }
    socket.send(JSON.stringify({ type: "initiateOffer" }));
}


startButton.addEventListener("click", init)
closeButton.addEventListener("click", closeConnection)

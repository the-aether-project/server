let videoPlayer = document.querySelector("#player")
let startButton = document.querySelector("#start")
let closeButton = document.querySelector("#close")
closeButton.disabled = true;

const socket = new WebSocket(ws_url);

socket.onopen = () => {
    console.log("Websocket initiated");
}

socket.onmessage = async (event) => {
    const data = JSON.parse(event.data);
    switch (data.type) {
        case 'offer':
            handleOffer(data.offer);
            break
        case 'msg':
            handleMsg(data.msg);
            break
    }
}

async function handleOffer(offer) {
    console.log("handle offer presents ", offer);

    let config = {
        sdpSemantics: 'unified-plan',
        iceServers: [{ urls: ['stun:stun.l.google.com:19302'] }]
    }

    try {
        const remoteOffer = new RTCSessionDescription(offer);
        const pc = new RTCPeerConnection(config);


        pc.addEventListener("track", (e) => {
            if (e.track.kind == "video") {
                videoPlayer.srcObject = e.streams[0];
                videoPlayer.play().catch((err) => { console.log("Cannot player videplayer, ", err) })
            }

            closeButton.disabled = false;
        })

        await pc.setRemoteDescription(remoteOffer);
        let answer = await pc.createAnswer();
        await pc.setLocalDescription(answer)

        socket.send(JSON.stringify({ type: "answer", payload: { sdp: pc.localDescription.sdp, type: pc.localDescription.type } }));
    } catch (error) {
        console.log("Error occured while handling offer", error);

    }
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
    console.log("Inbound message: ", msg);
}


function init() {
    if (!ws_url) {
        console.log("Websocket url not provided from server");
        return
    }
    console.log("Init called")
    socket.send(JSON.stringify({ type: "initiateOffer" }));
}


startButton.addEventListener("click", init)
closeButton.addEventListener("click", closeConnection)

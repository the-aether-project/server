const videoPlayer = document.querySelector("#player")
const startButton = document.querySelector("#start")
const closeButton = document.querySelector("#close")

closeButton.disabled = true;

const socket = new WebSocket(ws_url);
var pc = null;

socket.onopen = () => {
    console.log(`WebSocket connection established to server-obtained url: ${ws_url}`);
}

socket.onmessage = async (event) => {
    const data = JSON.parse(event.data);
    switch (data.type) {
        case 'negotiate':
            negotiate(data.stun_server);
            break
        case 'remoteDescription':
            pc.setRemoteDescription(data.answer);
            break
        case 'msg':
            handleMsg(data.msg);
    }
}


function negotiate(stun_server) {

    var config = {
        iceServers: [{ urls: [stun_server] }]
    }

    pc = new RTCPeerConnection(config);

    pc.addTransceiver('video', { direction: 'recvonly' });
    pc.addEventListener('track', (evt) => {
        if (evt.track.kind == 'video') {
            videoPlayer.srcObject = evt.streams[0];
            videoPlayer.play();
        }

        closeButton.disabled = false;
    });

    pc.createOffer().then((offer) => {
        return pc.setLocalDescription(offer);
    }).then(() => {
        return new Promise((resolve) => {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                const checkState = () => {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                };
                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }).then(() => {
        var offer = pc.localDescription;

        socket.send(
            JSON.stringify({
                'type': 'offer',
                'payload': {
                    sdp: offer.sdp,
                    type: offer.type,
                }
            })
        )
    }).catch((e) => {
        alert(e);
    });
}


function closeConnection() {
    console.log("Closing connection!")
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
    socket.send(JSON.stringify({ type: "startConnection" }));
}


startButton.addEventListener("click", init)
closeButton.addEventListener("click", closeConnection)

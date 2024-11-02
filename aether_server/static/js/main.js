const videoPlayer = document.querySelector("video#player")
const startButton = document.querySelector("button#start")
const closeButton = document.querySelector("button#close")

closeButton.disabled = true;

var pc = null;

function negotiate(socket, stun_server) {

    var config = {
        iceServers: [{ urls: [stun_server] }],
        bundlePolicy: "max-bundle",
    }

    pc = new RTCPeerConnection(config);

    pc.addTransceiver('video', { direction: 'recvonly' });
    pc.addEventListener('track', (evt) => {
        if (evt.track.kind == 'video') {
            videoPlayer.srcObject = evt.streams[0];
            videoPlayer.onloadedmetadata = () => {
                videoPlayer.style.height = "60vh";
                videoPlayer.style.aspectRatio = `${videoPlayer.videoWidth}/${videoPlayer.videoHeight}`;
                videoPlayer.controls = false;
            }

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


function closeConnection(socket) {
    console.log("Closing connection!")
    socket.send(
        JSON.stringify({
            type: "closeConnection"
        })
    )

    videoPlayer.srcObject.getTracks().forEach(track => track.stop());
    videoPlayer.srcObject = null;
    closeButton.removeEventListener("click", closeConnection)
    closeButton.disabled = true;
}

function handleMsg(msg) {
    console.log(`Inbound message: ${msg}`);
}


async function openConnection() {

    if (!ws_url) {
        console.error("Could not obtain websocket endpoint from the server.");
        return
    }

    const socket = new WebSocket(ws_url);

    socket.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        switch (data.type) {
            case 'negotiate':
                negotiate(socket, data.stun_server);
                break
            case 'remoteDescription':
                if (pc !== null) {
                    pc.setRemoteDescription(data.answer);
                } else {
                    console.error("Received remote description before creating the peer connection.")
                }
                break
            case 'msg':
                handleMsg(data.msg);
        }
    }

    await new Promise((resolve) => {
        if (socket.readyState === WebSocket.OPEN) {
            resolve();
        } else {
            socket.addEventListener('open', () => {
                console.log("Connection established to the server-provided websocket endpoint:", ws_url)
                resolve();
            });
        }
    })

    closeButton.addEventListener("click", () => closeConnection(socket))
    socket.send(JSON.stringify({ type: "startConnection" }));

    videoPlayer.addEventListener("click", (event) => {
        const rect = videoPlayer.getBoundingClientRect();
        const x_ratio = (event.clientX - rect.left) / rect.width;
        const y_ratio = (event.clientY - rect.top) / rect.height;

        const click_payload = { x_ratio, y_ratio };


        socket.send(
            JSON.stringify({
                type: "mouse",
                payload: { "clicked_at": click_payload },
            })
        );
    });
}


startButton.addEventListener("click", openConnection)

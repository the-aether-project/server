const videoPlayer = document.querySelector("video#player")
const startButton = document.querySelector("button#start")
const closeButton = document.querySelector("button#close")

closeButton.disabled = true;

const STUN_SERVER = "stun:stun.l.google.com:19302";


function openConnection() {

    var config = {
        iceServers: [{ urls: [STUN_SERVER] }],
        bundlePolicy: "max-bundle",
    }

    pc = new RTCPeerConnection(config);

    pc.addTransceiver('video', { direction: 'recvonly' });
    var dataChannel = pc.createDataChannel("mouse_events");

    const clickHandler = (event) => {

        const rect = videoPlayer.getBoundingClientRect();
        const x_ratio = (event.clientX - rect.left) / rect.width;
        const y_ratio = (event.clientY - rect.top) / rect.height;

        const click_payload = { x_ratio, y_ratio };

        dataChannel.send(
            JSON.stringify({
                type: "mouse",
                payload: { "clicked_at": click_payload },
            })
        );
    }

    dataChannel.onopen = () => {
        videoPlayer.addEventListener("click", clickHandler);
    }
    dataChannel.onclose = () => {
        videoPlayer.removeEventListener("click", clickHandler);
    }


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

        startButton.disabled = true;
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

        fetch(
            '/api/authorized/webrtc-offer',
            {
                method: 'POST',
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcm5hbWUiOiJqb2huX2RvZSIsImlhdCI6MTczNDUzNjk4NiwiZXhwIjoxNzM0NTM3NTg2fQ.xzsLQ57S7zCPpoViRd_DXuDMkrBb8mWDWYpRsvUvKZI",
                },
                body: JSON.stringify({
                    'sdp': offer.sdp,
                    'type': offer.type,
                }),
            }
        ).then((response) => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error("Failed to send offer to the server.")
            }
        }).then((data) => {
            pc.setRemoteDescription(data);
        }).catch((e) => {
            alert(e);
        }
        )

    }).catch((e) => {
        alert(e);
    });


    let closeHandler = () => {
        pc.close();

        videoPlayer.srcObject.getTracks().forEach(track => track.stop());
        videoPlayer.srcObject = null;
        closeButton.removeEventListener("click", closeHandler)
        closeButton.disabled = true;
        startButton.disabled = false;
    };

    closeButton.addEventListener("click", closeHandler)
}


startButton.addEventListener("click", openConnection)

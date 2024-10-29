let videoPlayer = document.querySelector("#videoplayer")
let startButton = document.querySelector("#start")


const socket = new WebSocket("http://localhost:7878/ws");


socket.onopen = () => {
    console.log("Websocket initiated")
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

    try {
        const remoteOffer = new RTCSessionDescription(offer);
        const pc = new RTCPeerConnection();


        pc.addEventListener("track", (e) => {
            console.log("got track that is , ", e);
            if (e.track.kind == "video") {
                videoPlayer.srcObject = e.streams[0];
                videoPlayer.play().catch((err) => { console.log("Cannot player videplayer, ", err) })
            }
        })

        await pc.setRemoteDescription(remoteOffer);
        let answer = await pc.createAnswer();
        await pc.setLocalDescription(answer)

        socket.send(JSON.stringify({ type: "answer", data: { sdp: pc.localDescription.sdp, type: pc.localDescription.type } }));
    } catch (error) {
        console.log("Error occured while handling offer", error);

    }
}

function handleMsg(msg) {
    console.log("Received : ", msg);
}


function init() {
    console.log("Init called")
    socket.send(JSON.stringify({ type: "initiateOffer" }));
}


startButton.addEventListener("click", init)
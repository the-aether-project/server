class AetherWebRTCView:
    async def post(self, landlords, ws_client, client_id, offer, landlord_id):
        try:
            # if landlord_id == client_id:
            #     return await ws_client.send_json(
            #         {"type": "ERROR", "message": "You can not rent your own device"}
            #     )

            selected_landlord = next(
                (
                    landlord
                    for landlord in landlords
                    if landlord["user_id"] == landlord_id
                ),
                None,
            )

            if selected_landlord is None or selected_landlord["active"]:
                return await ws_client.send_json(
                    {
                        "type": "ERROR",
                        "message": "Landlord is either not present or Already active with some other user",
                    }
                )

            ws_landlord = selected_landlord["ws"]
            if ws_landlord is None:
                return await ws_client.send_json(
                    {"type": "ERROR", "message": "Landlord is not active anymore"}
                )

            # TODO: UUID to identify the client_id
            # sending sdp offer to the landlord
            selected_landlord["ws_client"] = ws_client
            return await ws_landlord.send_json(
                {"type": "CONNECTION", "offer": offer, "uuid": str(client_id)}
            )
        except Exception as e:
            return await ws_client.send_json(
                {
                    "type": "ERROR",
                    "message": f"WebRTC connection failed from server {e}",
                }
            )

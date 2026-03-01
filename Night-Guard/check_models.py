from google import genai

# 請記得填入你的真實 API Key
client = genai.Client(api_key="AIzaSyDSId5qVigEBx8DsbRVAVPwtPfNIBh1RG4")

print("你的 API Key 支援以下模型：")
for model in client.models.list():
    print(model.name)
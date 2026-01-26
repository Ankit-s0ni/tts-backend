#!/usr/bin/env python3
"""Test Indian and other TTS voices with long text (2-3 pages)."""
import requests
import json
import time

BASE_URL = "http://localhost:8001"

# Long text for testing (~2500 characters - about 2-3 pages)
LONG_TEXT_EN = """
The advancement of artificial intelligence has revolutionized numerous industries and transformed the way we live and work. 
From healthcare diagnostics to autonomous vehicles, AI applications are becoming increasingly prevalent in our daily lives. 
However, this rapid growth also raises important questions about ethics, privacy, and the societal impact of automation.

Machine learning algorithms can now recognize patterns in massive datasets, enabling computers to learn and adapt without explicit programming. 
Natural language processing has made it possible for machines to understand and generate human language with remarkable accuracy. 
Computer vision systems can identify objects, recognize faces, and analyze visual information at speeds far exceeding human capabilities.

Despite these impressive achievements, several challenges remain. The interpretability of deep learning models remains a significant concern for critical applications. 
The potential displacement of workers due to automation necessitates comprehensive retraining and educational programs. 
Additionally, the concentration of AI capabilities in a few large technology companies raises questions about access and equity.

As we move forward, it is essential to ensure that AI development is guided by principles of transparency, accountability, and inclusivity. 
Collaboration between technologists, policymakers, and the public will be crucial in shaping a future where AI benefits society as a whole. 
The next decade will likely determine whether artificial intelligence becomes a tool for widespread prosperity or a source of increased inequality.
"""

LONG_TEXT_HI = """
कृत्रिम बुद्धिमत्ता का विकास आधुनिक समय की सबसे महत्वपूर्ण तकनीकी क्रांति है। स्वास्थ्य सेवा से लेकर परिवहन तक, 
कृत्रिम बुद्धिमत्ता के अनुप्रयोग हमारे दैनिक जीवन में तेजी से बढ़ रहे हैं। मशीन लर्निंग एल्गोरिदम बिना स्पष्ट 
निर्देशों के कंप्यूटर को सीखने और अनुकूल होने में सक्षम बनाते हैं।

प्राकृतिक भाषा प्रसंस्करण ने मशीनों को मानव भाषा को समझने और उत्पन्न करने की क्षमता दी है। कंप्यूटर दृष्टि प्रणालियां 
वस्तुओं को पहचान सकती हैं और मानव क्षमता से कहीं अधिक गति से दृश्य जानकारी का विश्लेषण कर सकती हैं। 
हालांकि, ये प्रभावशाली उपलब्धियां कई चुनौतियों के साथ आती हैं।

गहन शिक्षा मॉडल की व्याख्या करना महत्वपूर्ण अनुप्रयोगों के लिए एक महत्वपूर्ण चिंता है। स्वचालन के कारण कामगारों के 
विस्थापन से बचने के लिए व्यापक प्रशिक्षण कार्यक्रम आवश्यक हैं। इसके अलावा, कृत्रिम बुद्धिमत्ता की क्षमता कुछ 
बड़ी तकनीकी कंपनियों में केंद्रित होना भी चिंताजनक है।

आगे बढ़ते हुए, यह सुनिश्चित करना आवश्यक है कि कृत्रिम बुद्धिमत्ता का विकास पारदर्शिता, जवाबदेही और समावेशिता के 
सिद्धांतों से निर्देशित हो। तकनीकविद्, नीति निर्माता और जनता के बीच सहयोग भविष्य को आकार देने के लिए महत्वपूर्ण 
होगा। आने वाले दशक में कृत्रिम बुद्धिमत्ता व्यापक समृद्धि का एक साधन बनेगी या बढ़ती असमानता का कारण बनेगी, 
यह निर्धारित होगा।
"""

test_cases = [
    {"voice": "en_US-amy-medium", "text": LONG_TEXT_EN, "lang": "English (Amy)", "duration_est": "~30-40s"},
    {"voice": "hi_IN-pratham-medium", "text": LONG_TEXT_HI, "lang": "Hindi (Pratham)", "duration_est": "~35-45s"},
    {"voice": "hi_IN-priyamvada-medium", "text": LONG_TEXT_HI, "lang": "Hindi (Priyamvada - Female)", "duration_est": "~35-45s"},
]

print("=" * 70)
print("LONG TEXT TTS TEST (2-3 Pages)")
print("=" * 70)
print()

for i, test in enumerate(test_cases, 1):
    voice = test["voice"]
    text = test["text"]
    lang = test["lang"]
    duration_est = test["duration_est"]
    
    print(f"{i}. {lang} ({voice})")
    print(f"   Text length: {len(text)} characters ({len(text)//5} words approx)")
    print(f"   Estimated duration: {duration_est}")
    print(f"   Status: ", end="", flush=True)
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/tts/sync",
            json={"text": text, "voice": voice},
            timeout=60  # Long timeout for long text
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            duration = data.get("duration", 0)
            audio_size = len(data.get("audio", "")) // 2 / (1024 * 1024)  # MB
            
            print(f"✓ SUCCESS")
            print(f"   Actual duration: {duration:.2f}s")
            print(f"   Audio size: {audio_size:.2f} MB")
            print(f"   Processing time: {elapsed:.2f}s")
            print(f"   Sample rate: {data.get('sample_rate', '?')} Hz")
        else:
            error = response.json().get("detail", "Unknown error")
            print(f"✗ ERROR (Status {response.status_code})")
            print(f"   {error}")
    except requests.Timeout:
        print(f"✗ TIMEOUT (>60s)")
    except Exception as e:
        print(f"✗ EXCEPTION")
        print(f"   {str(e)[:80]}")
    
    print()

print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)

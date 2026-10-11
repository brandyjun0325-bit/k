import os, zipfile, shutil, re
from xml.etree import ElementTree as ET

SRC="temp/hwpx_job/original.hwpx"
OUT="temp/hwpx_job/final.hwpx"
ART="temp/hwpx_job/artifact_hwpx"

def local(tag):
    return tag.rsplit("}",1)[-1] if "}" in tag else tag

def ptext(p):
    return "".join((x.text or "") for x in p.iter() if local(x.tag)=="t")

def set_ptext(p, s):
    ts=[x for x in p.iter() if local(x.tag)=="t"]
    if not ts:
        return False
    ts[0].text=s
    for x in ts[1:]:
        x.text=""
    return True

def alltext(el):
    return "".join((x.text or "") for x in el.iter() if local(x.tag)=="t")

# Preserve namespace prefixes as much as ElementTree permits.
with zipfile.ZipFile(SRC,"r") as z:
    section_names=[n for n in z.namelist() if n.startswith("Contents/section") and n.endswith(".xml")]
    modified={}
    found_cut=False
    verify_changes=[]

    for name in section_names:
        raw=z.read(name)
        # register namespaces from this XML
        try:
            import io
            for ev, ns in ET.iterparse(io.BytesIO(raw), events=("start-ns",)):
                prefix, uri=ns
                try:
                    ET.register_namespace(prefix or "", uri)
                except Exception:
                    pass
        except Exception:
            pass
        root=ET.fromstring(raw)

        # Cut everything beginning with the 13~14 detailed guide.
        direct=list(root)
        cut_index=None
        for i,ch in enumerate(direct):
            if "13~14차시 지도안" in alltext(ch):
                cut_index=i
                break
        if cut_index is not None:
            for ch in direct[cut_index:]:
                root.remove(ch)
            found_cut=True

        current=None
        for p in [e for e in root.iter() if local(e.tag)=="p"]:
            t=ptext(p)
            if "1~2차시 지도안" in t: current="1-2"; continue
            if "3~4차시 지도안" in t: current="3-4"; continue
            if "5~6차시 지도안" in t: current="5-6"; continue
            if "7~8차시 지도안" in t: current="7-8"; continue
            if "9~10차시 지도안" in t: current="9-10"; continue
            if "11~12차시 지도안" in t: current="11-12"; continue

            new=None

            if current=="1-2":
                if "※ 글씨 쓰기가 서툰 학생은 그림" in t:
                    new=("※ 글씨 쓰기가 서툰 학생은 그림 위주로 표현하도록 격려합니다.\n"
                         "※ 소규모 학급이거나 시간이 남는 경우, A4 도화지에 ‘이야기 무대·친구 이야기 듣는 자리·칭찬 우체통’을 표시하는 "
                         "‘우리 반 이야기 놀이터 지도 그리기’를 5~10분 선택 활동으로 운영합니다.")
            elif current=="3-4":
                if "■ 직접 만든 '리액션 팻말'을 번쩍 들며" in t:
                    new="■ 직접 만든 ‘리액션 팻말’을 알맞은 타이밍에 조용히 들어 친구의 말에 반응할 수 있다."
                elif '[3단계] 가장 큰 소리로 "우와!", "아하!"' in t:
                    new='- [3단계] 상황에 맞는 밝은 목소리로 "우와!", "아하!" 추임새 넣기'
                elif "직접만든 리액션 팻말을 번쩍 들며 큰 소리로 환호" in t.replace(" ",""):
                    new=("◾ [핵심 미션] 듣는 친구들은 눈을 맞추며 끝까지 듣고, 친구의 말이 끝난 뒤 알맞은 순간에 "
                         "리액션 팻말을 조용히 한 번 들어 ‘우와!’, ‘아하!’처럼 짧게 반응합니다.")
                elif "※ 엉뚱한" in t and "말하기의 두려움" in t:
                    new=("※ 엉뚱한 대답이나 아주 짧은 발표라도 따뜻하게 반응하여 말하기의 두려움을 줄입니다.\n"
                         "※ 팻말은 흔들거나 책상을 두드리지 않고, 친구의 말이 끝난 뒤 한 번만 듭니다.\n"
                         "※ 시간이 남으면 짝꿍이 말할 때 미소·엄지·끄덕임으로만 반응하는 ‘리액션 몸짓 거울 놀이’를 5분 정도 운영합니다.")
            elif current=="5-6":
                if "■ 친구의 눈을 바라보며 자신 있게 자기소개" in t:
                    new="■ 친구의 상상을 존중하며 소리에 어울리는 이야기를 함께 만들 수 있다."
                elif "★ 준비물:" in t and ("소리 음원" in t or "스피커" in t):
                    new="★ 준비물: 소리 음원, 스피커, 장소·인물 그림 힌트 카드, 장난감 마이크"
                elif "이번에는 소리만 듣고 어떤 상황인지 구체적으로 상상해서 말" in t:
                    new=("■ 먼저 소리만 듣고 어떤 상황인지 자유롭게 상상해 말합니다. "
                         "장면이 잘 떠오르지 않는 학생에게는 집·학교·숲·기차역 등의 장소 카드나 요리사·경찰관·우주인·가족 등의 인물 카드 중 "
                         "2~4장을 제시하여 ‘어디에서 → 누가 → 무엇을 했을까?’ 순서로 상상의 뼈대를 만들도록 돕습니다.")
                elif "※ 시각적 자극을 차단하고 청각에만" in t.replace(" ",""):
                    new=("※ 첫 번째 듣기에서는 소리에 집중하되, 상상이 어려운 학생에게는 두 번째 시도부터 장소·인물 그림 힌트를 선택적으로 제공합니다. "
                         "힌트는 정답을 알려 주는 자료가 아니라 상상을 시작하게 돕는 발판으로 활용합니다.")
            elif current=="7-8":
                if "★ 준비물:" in t and "감정 카드" in t:
                    new="★ 준비물: 감정 카드 세트, 감정 미니그림책, 활동지, 센터 기본 제공 필기도구"
                elif "▶ 동기유발: 표정 퀴즈! 선생님 얼굴 읽기" in t:
                    new="▶ 동기유발: 감정 미니그림책으로 마음 읽기"
                elif "선생님이 아무 말 없이 얼굴 표정만으로" in t:
                    new=("■ 감정 미니그림책의 짧은 장면을 한 장씩 보여 주고, 그림 속 인물의 표정·몸짓·상황을 살펴 어떤 마음인지 맞혀 봅니다. "
                         "그 뒤 교사가 같은 감정을 표정으로 표현해 학생들이 다시 확인합니다.")
                elif "실전! 내 마음을 맞춰봐 스피드 퀴즈" in t:
                    new=t.replace("실전! 내 마음을 맞춰봐 스피드 퀴즈","실전! 모두 함께 내 마음을 맞춰봐")
                elif "모둠별(4~5인)로 둥글게 모여 앉은 뒤" in t:
                    new=("■ 모둠 경쟁 대신 교사 주도 전체 활동으로 진행합니다. 학생들은 제자리에서 발표 친구를 바라보고, "
                         "교사가 한 명씩 발표 학생을 정해 감정 카드 한 장을 보여 줍니다.")
                elif "술래는 소리를 내지 않고 오직 표정과 몸짓으로만" in t:
                    new=("■ 발표 학생은 감정 단어를 말하지 않고 표정과 몸짓으로 표현합니다. 나머지 학생은 교사의 신호가 나온 뒤 "
                         "손 신호나 감정 카드를 들어 동시에 답하여 먼저 외치는 경쟁이 되지 않도록 합니다.")
                elif "정답을 맞힌 후에는 다 함께" in t:
                    new=("■ 답을 확인한 뒤에는 다 함께 “그랬구나!”, “그럴 수 있어!”와 같이 공감하는 말을 하며, "
                         "같은 상황에서도 서로 다른 감정을 느낄 수 있음을 존중합니다.")
            elif current=="9-10":
                if t.strip()=="[티키타카] 꼬리에 꼬리를 무는 기차":
                    new="[2단계: 티키타카] 꼬리에 꼬리를 무는 기차"
                elif "'[2단계: 티키타카] 꼬리에 꼬리를 무는 기차'" in t:
                    # already official in teacher line; leave
                    pass
                elif "■ 끝말잇기를 할 때 단어만 말하는 것이 아니라" in t:
                    new=("■ 끝말잇기를 할 때 단어만 말하는 것이 아니라, 그 단어에 어울리는 간단한 상체 동작을 함께 표현합니다. "
                         "학생은 기차 대형으로 교실을 돌지 않고 의자 옆 ‘내 자리 발자국’ 안에서만 움직입니다.")
                elif "■ 몸을 함께 움직이며 또래 간의 활발한 언어적, 신체적 상호작용" in t:
                    new=("■ 동작은 친구와 닿지 않을 만큼 작고 분명하게 하며, 교사가 손을 들거나 ‘멈춤’ 신호를 주면 즉시 멈춥니다. "
                         "말과 동작의 재미는 살리되 이동은 최소화합니다.")
                elif "※ 단어를 틀리거나 막히더라도 절대" in t:
                    new=("※ 단어를 틀리거나 막히더라도 놀리지 않고 ‘괜찮아!’라고 응원합니다.\n"
                         "※ 활동 3에서는 기차 대형 이동을 하지 않으며, 의자 옆 개인 공간을 벗어나지 않도록 안전 규칙을 먼저 확인합니다.")
            elif current=="11-12":
                if "■ 무작위 단어 카드 3장을 뽑아 상상력을 발휘하여 짧은 문장을 만들 수 있다." in t:
                    new="■ 무작위 단어 카드 3장을 보며 상상력을 발휘하여 짧은 문장을 말로 만들 수 있다."
                elif "■ 뽑힌 3개의 단어를 모두 사용하여 어떻게든 말이 이어지는 짧은 문장" in t:
                    new=("■ 뽑힌 3개의 단어를 모두 사용하여 뜻이 통하는 짧은 문장을 먼저 말로 만들어 모둠 친구들에게 들려줍니다. "
                         "긴 문장을 활동지에 완성해서 쓰도록 요구하지 않습니다.")
                elif "■ 모둠별로 릴레이를 통해 완성된 가장 재미있고 엉뚱한 동화를 다른 모둠" in t:
                    new=("■ 모둠별로 릴레이를 통해 완성된 이야기를 그림 카드와 핵심 단어를 보며 다른 모둠 친구들 앞에서 말로 발표합니다. "
                         "말하기가 어려운 학생은 카드 들기·그림 보여 주기·효과음 역할로 참여할 수 있습니다.")
                elif "※ 쓰기나 읽기에 대한" in t and "입과 귀" in t:
                    new=("※ 쓰기나 읽기에 대한 진입 장벽을 낮추고 입과 귀를 활용하는 놀이에 집중합니다. "
                         "기록이 필요한 경우에도 긴 문장 대신 핵심 장면 그림과 한두 단어만 남기도록 합니다.")

            if new is not None:
                old=t
                if set_ptext(p,new):
                    verify_changes.append((current, old[:80], new[:80]))

        modified[name]=ET.tostring(root, encoding="utf-8", xml_declaration=True)

    if not found_cut:
        raise RuntimeError("Could not find 13~14차시 지도안 cut point")

    # Build final HWPX preserving original members/metadata; changed XML only.
    with zipfile.ZipFile(OUT,"w") as out:
        for info in z.infolist():
            data=modified.get(info.filename, z.read(info.filename))
            # Preserve mimetype as stored and preserve original compression for all entries.
            zi=zipfile.ZipInfo(info.filename, date_time=info.date_time)
            zi.compress_type=info.compress_type
            zi.comment=info.comment
            zi.extra=info.extra
            zi.internal_attr=info.internal_attr
            zi.external_attr=info.external_attr
            zi.create_system=info.create_system
            out.writestr(zi,data)

# Validate final zip and text.
with zipfile.ZipFile(OUT,"r") as z:
    bad=z.testzip()
    if bad:
        raise RuntimeError("Corrupt zip member: "+bad)
    texts=[]
    for n in z.namelist():
        if n.startswith("Contents/section") and n.endswith(".xml"):
            root=ET.fromstring(z.read(n))
            texts.append("".join((x.text or "") for x in root.iter() if local(x.tag)=="t"))
    full="\n".join(texts)
    required=[
        "1~2차시 지도안","11~12차시 지도안",
        "우리 반 이야기 놀이터 지도 그리기",
        "장소·인물 그림 힌트 카드",
        "[2단계: 티키타카] 꼬리에 꼬리를 무는 기차",
        "짧은 문장을 말로 만들 수 있다."
    ]
    missing=[s for s in required if s not in full]
    if missing:
        raise RuntimeError("Missing revised text: "+repr(missing))
    if "13~14차시 지도안" in full:
        raise RuntimeError("13~14 detailed guide still present")

# Unpack the final HWPX so GitHub artifact ZIP itself can be used as an HWPX package.
if os.path.exists(ART):
    shutil.rmtree(ART)
os.makedirs(ART,exist_ok=True)
with zipfile.ZipFile(OUT,"r") as z:
    z.extractall(ART)

print("HWPX BUILD OK")
print("changes", len(verify_changes))
for x in verify_changes:
    print(x[0], ":", x[1].replace("\n"," ")[:70], "=>", x[2].replace("\n"," ")[:70])
print("final_size", os.path.getsize(OUT))

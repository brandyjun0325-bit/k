import os, zipfile, shutil, io
from xml.etree import ElementTree as ET

SRC="temp/hwpx_job/original.hwpx"
OUT="temp/hwpx_job/final.hwpx"
ART="temp/hwpx_job/artifact_hwpx"

def local(tag):
    return tag.rsplit("}",1)[-1] if "}" in tag else tag

def all_tnodes(root):
    return [x for x in root.iter() if local(x.tag)=="t"]

def alltext(root):
    return "".join((x.text or "") for x in all_tnodes(root))

def replace_global_once(root, old, new):
    ts=all_tnodes(root)
    vals=[x.text or "" for x in ts]
    full="".join(vals)
    idx=full.find(old)
    if idx<0:
        return False
    end=idx+len(old)
    pos=0
    s_i=e_i=None
    s_off=e_off=None
    for i,v in enumerate(vals):
        st=pos; en=pos+len(v)
        if s_i is None and idx < en:
            s_i=i; s_off=idx-st
        if s_i is not None and end <= en:
            e_i=i; e_off=end-st
            break
        pos=en
    if s_i is None or e_i is None:
        return False
    if s_i==e_i:
        v=vals[s_i]
        ts[s_i].text=v[:s_off]+new+v[e_off:]
    else:
        ts[s_i].text=vals[s_i][:s_off]+new
        for j in range(s_i+1,e_i):
            ts[j].text=""
        ts[e_i].text=vals[e_i][e_off:]
    return True

def replace_global_all(root, old, new, maxn=10):
    c=0
    while c<maxn and replace_global_once(root,old,new):
        c+=1
    return c

def replace_variants(root, olds, new):
    total=0
    for old in olds:
        total += replace_global_all(root,old,new)
    return total

repls=[
("1-2 optional-map",
 ["※ 글씨 쓰기가 서툰 학생은 그림 위주로 표현하도록 격려합니다."],
 "※ 글씨 쓰기가 서툰 학생은 그림 위주로 표현하도록 격려합니다. ※ 시간이 남으면 A4 도화지에 ‘이야기 무대·친구 이야기 듣는 자리·칭찬 우체통’을 표시하는 ‘우리 반 이야기 놀이터 지도 그리기’를 5~10분 선택 활동으로 운영합니다."),

("3-4 goal",
 ["■ 직접 만든 '리액션 팻말'을 번쩍 들며 생동감 넘치게 반응할 수 있다."],
 "■ 직접 만든 ‘리액션 팻말’을 알맞은 타이밍에 조용히 들어 친구의 말에 반응할 수 있다."),

("3-4 reaction-step",
 ['- [3단계] 가장 큰 소리로 "우와!", "아하!" 추임새 넣기'],
 '- [3단계] 상황에 맞는 밝은 목소리로 "우와!", "아하!" 추임새 넣기'),

("3-4 mission",
 ["◾ [핵심 미션] 듣는 친구들은 눈을 맞추며 듣다가, 재미있는 부분에서 직접 만든 리액션 팻말을 번쩍 들며 큰 소리로 환호해 줍니다."],
 "◾ [핵심 미션] 듣는 친구들은 눈을 맞추며 끝까지 듣고, 친구의 말이 끝난 뒤 알맞은 순간에 리액션 팻말을 조용히 한 번 들어 ‘우와!’, ‘아하!’처럼 짧게 반응합니다."),

("3-4 note",
 ["※ 엉뚱한 대답이나 아주 짧은 발표라도 완벽한 리액션을 보내주어 말하기의 두려움을 없애줍니다."],
 "※ 엉뚱한 대답이나 아주 짧은 발표라도 따뜻하게 반응하여 말하기의 두려움을 줄입니다. 팻말은 흔들거나 책상을 두드리지 않고, 친구의 말이 끝난 뒤 한 번만 듭니다. 시간이 남으면 짝꿍의 말에 미소·엄지·끄덕임으로만 반응하는 ‘리액션 몸짓 거울 놀이’를 5분 정도 운영합니다."),

("5-6 goal",
 ["■ 친구의 눈을 바라보며 자신 있게 자기소개를 할 수 있다."],
 "■ 친구의 상상을 존중하며 소리에 어울리는 이야기를 함께 만들 수 있다."),

("5-6 materials",
 ["★ 준비물:소리 음원,스피커","★ 준비물: 소리 음원,스피커","★ 준비물: 소리 음원, 스피커"],
 "★ 준비물: 소리 음원, 스피커, 장소·인물 그림 힌트 카드, 장난감 마이크"),

("5-6 visual-hint",
 ["■ 이번에는 소리만 듣고 어떤 상황인지 구체적으로 상상해서 말해봅니다."],
 "■ 먼저 소리만 듣고 어떤 상황인지 자유롭게 상상해 말합니다. 장면이 잘 떠오르지 않는 학생에게는 집·학교·숲·기차역 등의 장소 카드나 요리사·경찰관·우주인·가족 등의 인물 카드 중 2~4장을 제시하여 ‘어디에서 → 누가 → 무엇을 했을까?’ 순서로 상상의 뼈대를 만들도록 돕습니다."),

("7-8 materials",
 ["★ 준비물: 감정 카드 세트","★ 준비물:감정 카드 세트"],
 "★ 준비물: 감정 카드 세트, 감정 미니그림책, 활동지, 센터 기본 제공 필기도구"),

("7-8 intro-title",
 ["▶ 동기유발: 표정 퀴즈! 선생님 얼굴 읽기"],
 "▶ 동기유발: 감정 미니그림책으로 마음 읽기"),

("7-8 intro-detail",
 ["■ 선생님이 아무 말 없이 얼굴 표정만으로 기쁨, 슬픔, 화남, 놀람 등의 감정을 과장되게 지어 보이고, 아이들이 선생님의 기분이 어떤지 맞혀보게 합니다."],
 "■ 감정 미니그림책의 짧은 장면을 한 장씩 보여 주고, 그림 속 인물의 표정·몸짓·상황을 살펴 어떤 마음인지 맞혀 봅니다. 그 뒤 교사가 같은 감정을 표정으로 표현해 학생들이 다시 확인합니다."),

("7-8 activity-title",
 ["▶ [활동3] 실전! 내 마음을 맞춰봐 스피드 퀴즈 (20분)"],
 "▶ [활동3] 실전! 모두 함께 내 마음을 맞춰봐 (20분)"),

("7-8 whole-class",
 ["■ 모둠별(4~5인)로 둥글게 모여 앉은 뒤, 모둠원 중 한 명이 술래가 되어 감정 카드를 한 장 뽑습니다."],
 "■ 모둠 경쟁 대신 교사 주도 전체 활동으로 진행합니다. 학생들은 제자리에서 발표 친구를 바라보고, 교사가 한 명씩 발표 학생을 정해 감정 카드 한 장을 보여 줍니다."),

("7-8 simultaneous-answer",
 ["■ 술래는 소리를 내지 않고 오직 표정과 몸짓으로만 카드의 감정을 설명하고, 나머지 친구들은 어떤 감정인지 맞힙니다."],
 "■ 발표 학생은 감정 단어를 말하지 않고 표정과 몸짓으로 표현합니다. 나머지 학생은 교사의 신호가 나온 뒤 손 신호나 감정 카드를 들어 동시에 답하여 먼저 외치는 경쟁이 되지 않도록 합니다."),

("7-8 empathy",
 ['■ 정답을 맞힌 후에는 다 함께 "맞아! 그럴 때 정말 (기쁘지/슬프지)!"라고 호응해 주며 공감하는 리액션을 실천합니다.'],
 '■ 답을 확인한 뒤에는 다 함께 “그랬구나!”, “그럴 수 있어!”와 같이 공감하는 말을 하며, 같은 상황에서도 서로 다른 감정을 느낄 수 있음을 존중합니다.'),

("9-10 topic",
 ["[티키타카] 꼬리에 꼬리를 무는 기차"],
 "[2단계: 티키타카] 꼬리에 꼬리를 무는 기차"),

("9-10 movement",
 ["■ 끝말잇기를 할 때 단어만 말하는 것이 아니라, 그 단어에 어울리는 재미있는 '동작'을 함께 추가하여 말합니다."],
 "■ 끝말잇기를 할 때 단어만 말하는 것이 아니라, 그 단어에 어울리는 간단한 상체 동작을 함께 표현합니다. 학생은 기차 대형으로 교실을 돌지 않고 의자 옆 ‘내 자리 발자국’ 안에서만 움직입니다."),

("9-10 movement-safety",
 ["■ 몸을 함께 움직이며 또래 간의 활발한 언어적, 신체적 상호작용을 촉진합니다."],
 "■ 동작은 친구와 닿지 않을 만큼 작고 분명하게 하며, 교사가 손을 들거나 ‘멈춤’ 신호를 주면 즉시 멈춥니다. 말과 동작의 재미는 살리되 이동은 최소화합니다."),

("11-12 goal",
 ["■ 무작위 단어 카드 3장을 뽑아 상상력을 발휘하여 짧은 문장을 만들 수 있다."],
 "■ 무작위 단어 카드 3장을 보며 상상력을 발휘하여 짧은 문장을 말로 만들 수 있다."),

("11-12 oral-sentence",
 ["■ 뽑힌 3개의 단어를 모두 사용하여 어떻게든 말이 이어지는 짧은 문장을 하나씩 만들어 모둠 친구들에게 이야기해 봅니다."],
 "■ 뽑힌 3개의 단어를 모두 사용하여 뜻이 통하는 짧은 문장을 먼저 말로 만들어 모둠 친구들에게 들려줍니다. 긴 문장을 활동지에 완성해서 쓰도록 요구하지 않습니다."),

("11-12 oral-presentation",
 ["■ 모둠별로 릴레이를 통해 완성된 가장 재미있고 엉뚱한 동화를 다른 모둠 친구들 앞에서 발표해 봅니다."],
 "■ 모둠별로 릴레이를 통해 완성된 이야기를 그림 카드와 핵심 단어를 보며 다른 모둠 친구들 앞에서 말로 발표합니다. 말하기가 어려운 학생은 카드 들기·그림 보여 주기·효과음 역할로 참여할 수 있습니다."),

("11-12 oral-note",
 ["※ 쓰기나 읽기에 대한 진입 장벽을 완벽히 덜어내고 오직 입과 귀를 활용하는 놀이에 집중합니다."],
 "※ 쓰기나 읽기에 대한 진입 장벽을 낮추고 입과 귀를 활용하는 놀이에 집중합니다. 기록이 필요한 경우에도 긴 문장 대신 핵심 장면 그림과 한두 단어만 남기도록 합니다.")
]

changes=[]
with zipfile.ZipFile(SRC,"r") as zin:
    modified={}
    found_cut=False
    for name in zin.namelist():
        if not (name.startswith("Contents/section") and name.endswith(".xml")):
            continue
        raw=zin.read(name)
        try:
            for _,ns in ET.iterparse(io.BytesIO(raw),events=("start-ns",)):
                prefix,uri=ns
                try: ET.register_namespace(prefix or "",uri)
                except: pass
        except: pass
        root=ET.fromstring(raw)

        # Remove detailed 13~48 material.
        direct=list(root)
        cut=None
        for i,ch in enumerate(direct):
            if "13~14차시 지도안" in alltext(ch):
                cut=i; break
        if cut is not None:
            for ch in direct[cut:]:
                root.remove(ch)
            found_cut=True

        for label,olds,new in repls:
            n=replace_variants(root,olds,new)
            if n:
                changes.append((label,n))

        modified[name]=ET.tostring(root,encoding="utf-8",xml_declaration=True)

    if not found_cut:
        raise RuntimeError("13~14 cut point not found")

    with zipfile.ZipFile(OUT,"w") as zout:
        for info in zin.infolist():
            data=modified.get(info.filename,zin.read(info.filename))
            zi=zipfile.ZipInfo(info.filename,date_time=info.date_time)
            zi.compress_type=info.compress_type
            zi.comment=info.comment
            zi.extra=info.extra
            zi.internal_attr=info.internal_attr
            zi.external_attr=info.external_attr
            zi.create_system=info.create_system
            zout.writestr(zi,data)

with zipfile.ZipFile(OUT,"r") as z:
    bad=z.testzip()
    if bad: raise RuntimeError("bad zip member "+bad)
    full=[]
    for n in z.namelist():
        if n.startswith("Contents/section") and n.endswith(".xml"):
            rt=ET.fromstring(z.read(n))
            full.append(alltext(rt))
    full="\n".join(full)

must=[
"1~2차시 지도안","11~12차시 지도안",
"우리 반 이야기 놀이터 지도 그리기",
"알맞은 타이밍에 조용히 들어",
"장소·인물 그림 힌트 카드",
"감정 미니그림책으로 마음 읽기",
"실전! 모두 함께 내 마음을 맞춰봐",
"[2단계: 티키타카] 꼬리에 꼬리를 무는 기차",
"내 자리 발자국",
"짧은 문장을 말로 만들 수 있다.",
"긴 문장을 활동지에 완성해서 쓰도록 요구하지 않습니다."
]
missing=[x for x in must if x not in full]
if missing: raise RuntimeError("missing required revisions: "+repr(missing))
if "13~14차시 지도안" in full: raise RuntimeError("13~14 still present")

core=[
"▶ [활동1] 좋은 리액션 3종 세트 연습하기",
"▶ [활동2] 꼬리에 꼬리를 무는 상상 더하기",
'▶ [활동2] "나는 ~할 때 ~해" 맥락에 맞게 경험 말하기',
"▶ [활동1] 기본 끝말잇기와 순서 지키기",
"▶ [활동2] 돌아가며 한 문장씩 보태어 엉뚱한 동화 짓기"
]
lost=[x for x in core if x not in full]
if lost: raise RuntimeError("core text lost: "+repr(lost))

if os.path.exists(ART): shutil.rmtree(ART)
os.makedirs(ART,exist_ok=True)
with zipfile.ZipFile(OUT,"r") as z:
    z.extractall(ART)

print("HWPX BUILD OK")
print("changes",changes)
print("final_size",os.path.getsize(OUT))

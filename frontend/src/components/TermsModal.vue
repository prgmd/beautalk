<script setup>
const props = defineProps({
  type: {
    type: String, // 'terms' | 'privacy'
    required: true,
  },
})

const emit = defineEmits(['close'])

const CONTENT = {
  terms: {
    title: '이용약관',
    sections: [
      {
        heading: '제1조 (목적)',
        body: '이 약관은 beautalk(이하 "회사")가 제공하는 챗봇 기반 화장품 추천 서비스(이하 "서비스")의 이용과 관련하여 회사와 이용자 간의 권리, 의무 및 책임사항을 규정함을 목적으로 합니다.',
      },
      {
        heading: '제2조 (서비스의 제공)',
        body: '회사는 이용자가 입력한 피부 정보 및 대화 내용을 바탕으로 화장품을 추천하는 서비스를 제공합니다. 추천 결과는 참고 정보이며, 제품 구매 및 사용에 대한 최종 판단과 책임은 이용자에게 있습니다.',
      },
      {
        heading: '제3조 (이용자의 의무)',
        body: '이용자는 회원가입 시 사실에 기반한 정보를 입력해야 하며, 타인의 정보를 도용하거나 서비스를 부정한 목적으로 이용해서는 안 됩니다.',
      },
      {
        heading: '제4조 (서비스 이용의 제한)',
        body: '이용자가 관련 법령 또는 본 약관을 위반한 경우, 회사는 사전 통지 없이 서비스 이용을 제한하거나 회원 자격을 정지·상실시킬 수 있습니다.',
      },
      {
        heading: '제5조 (약관의 변경)',
        body: '회사는 필요한 경우 관련 법령을 위반하지 않는 범위에서 본 약관을 변경할 수 있으며, 변경 시 서비스 내 공지를 통해 안내합니다.',
      },
    ],
  },
  privacy: {
    title: '개인정보처리방침',
    sections: [
      {
        heading: '1. 수집하는 개인정보 항목',
        body: '회사는 회원가입 및 서비스 제공을 위해 이메일, 비밀번호(또는 SNS 계정 식별자), 피부 타입·피부 고민·기피 성분 등 피부 프로필 정보, 챗봇 대화 및 이용 기록을 수집합니다.',
      },
      {
        heading: '2. 개인정보의 수집 및 이용목적',
        body: '수집한 정보는 회원 식별 및 로그인, 맞춤형 화장품 추천 제공, 찜한 제품·추천 이력 관리, 서비스 개선을 위한 분석 목적으로 이용됩니다.',
      },
      {
        heading: '3. 개인정보의 보유 및 이용기간',
        body: '회원 탈퇴 시 관련 법령에서 별도로 보존을 요구하는 경우를 제외하고, 수집된 개인정보는 지체 없이 파기됩니다.',
      },
      {
        heading: '4. 개인정보의 제3자 제공',
        body: '회사는 이용자의 동의가 있거나 법령에 근거가 있는 경우를 제외하고 개인정보를 외부에 제공하지 않습니다.',
      },
      {
        heading: '5. 이용자의 권리',
        body: '이용자는 마이페이지를 통해 자신의 피부 프로필 정보를 언제든지 조회·수정할 수 있으며, 회원 탈퇴를 통해 개인정보 삭제를 요청할 수 있습니다.',
      },
    ],
  },
}
</script>

<template>
  <Transition name="modal">
    <div class="overlay" @click="emit('close')">
      <div class="modal" @click.stop>
        <button class="close-btn" @click="emit('close')">×</button>
        <h2 class="title">{{ CONTENT[type].title }}</h2>
        <div class="body">
          <section v-for="sec in CONTENT[type].sections" :key="sec.heading" class="section">
            <h3 class="section-title">{{ sec.heading }}</h3>
            <p class="section-body">{{ sec.body }}</p>
          </section>
        </div>
        <button class="confirm-btn" @click="emit('close')">확인</button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 24px;
}

.modal {
  background: var(--surface);
  border-radius: 18px;
  width: 100%;
  max-width: 480px;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;
  padding: 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.close-btn {
  position: absolute;
  top: 14px;
  right: 16px;
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 50%;
  font-size: 20px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
}
.close-btn:hover { background: rgba(0, 0, 0, 0.08); }

.title { font-size: 18px; font-weight: 700; padding-right: 32px; }

.body { display: flex; flex-direction: column; gap: 16px; }

.section { display: flex; flex-direction: column; gap: 6px; }
.section-title { font-size: 14px; font-weight: 600; }
.section-body { font-size: 13px; line-height: 1.7; color: var(--text-secondary); }

.confirm-btn {
  align-self: flex-end;
  padding: 10px 24px;
  background: var(--text-primary);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

/* Transition */
.modal-enter-active, .modal-leave-active { transition: opacity 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-active .modal, .modal-leave-active .modal { transition: transform 0.2s; }
.modal-enter-from .modal, .modal-leave-to .modal { transform: scale(0.96); }
</style>

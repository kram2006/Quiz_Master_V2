// Vue 3 app for quiz attempt page
const { createApp } = Vue;

if (document.getElementById('app')) {
    createApp({
        data() {
            return {
                questions: window.quizData?.questions || [],
                answers: {},
            };
        },
        mounted() {
            // Optionally, prefill answers if needed
        },
        methods: {
            // Add any methods if needed
        }
    }).mount('#app');
} 
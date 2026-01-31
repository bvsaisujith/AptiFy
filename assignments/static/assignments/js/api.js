const API_BASE = '/api/assignments';

// Helper for Fetch with CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

async function apiCall(endpoint, method = 'GET', data = null) {
    const headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
    };

    const config = {
        method: method,
        headers: headers,
    };

    if (data) {
        config.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, config);
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error("API Call Failed:", error);
        throw error;
    }
}

const AssignmentAPI = {
    start: async (assignmentId) => {
        return await apiCall('/start', 'POST', { assignment_id: assignmentId });
    },
    submitQuiz: async (attemptId, questionId, selectedOptionId) => {
        return await apiCall('/quiz/submit', 'POST', {
            attempt_id: attemptId,
            question_id: questionId,
            selected_option_id: selectedOptionId
        });
    },
    submitOutput: async (attemptId, questionId, predictedOutput) => {
        return await apiCall('/output/submit', 'POST', {
            attempt_id: attemptId,
            question_id: questionId,
            predicted_output: predictedOutput
        });
    },
    submitCode: async (attemptId, questionId, code, executionTime, complexity, passedPct, codeRuns) => {
        return await apiCall('/code/submit', 'POST', {
            attempt_id: attemptId,
            question_id: questionId,
            code: code,
            execution_time: executionTime,
            complexity_rank: complexity,
            testcases_passed_percentage: passedPct,
            code_runs: codeRuns
        });
    },
    getSummary: async (attemptId) => {
        return await apiCall(`/${attemptId}/summary`, 'GET');
    }
};

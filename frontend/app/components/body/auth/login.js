import { loggedFetch, redirect } from '../../../engine/utils.js';
import { error } from '../../../engine/error.js';
import { getLanguageDict } from '../../../engine/language.js';
import { loginOTP } from '../otp/loginOTP.js';
import { redirectToIntraApi } from './oauth.js';

export const loginRequest = async (username, password, render, div) => {
    if (!username || !password) {
        return;
    }
    const response = await loggedFetch(fetch)('/api/auth/login/', {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    });
    if (response.status === 423)
        return await loginOTP(render, div, username, password);
    if (response.status !== 200) {
        switch (response.status) {
            case 404:
                error('Invalid username or password', 'warning');
                break;
            case 401:
                error('Invalid username or password', 'warning');
                break;
            default:
                error('Unknown error', 'danger');
                break;
        }
        return ;
    }
    return await redirect('/', true);
};

export const login = (render, div) => {
    const language = localStorage.getItem('language') || 'en';
    const data = getLanguageDict(language, 'auth');

    render(div, `
    <style>
        .loginForm {
            margin-top: 5vh;
        }

    </style>
        <div class="row loginForm">
            <form>
                <div class="mb-3">
                    <label for="usernameValue" class="form-label">${data.username}</label>
                    <input type="text" class="form-control" id="usernameValue" required>
                </div>
                <div class="mb-3">
                    <label for="passwordValue" class="form-label">${data.password}</label>
                    <input type="password" class="form-control" id="passwordValue" required>
                </div>
            </form>
            <div class="mb-3 text-center">
                <input type="submit" class="btn button w-100" id="toLoginButton" value="${data.login}"></input>
            </div>
            <div class="mb-3 text-center">
                <span class="text-muted">${data.or}</span>
            </div>
            <div class="mb-3 text-center">
                <button type="button" class="btn button w-100" id="toOAuthLoginButton">${data.Ologin}</button>
            </div>
        </div>
    `);

    const toLoginButton = document.getElementById('toLoginButton');
    const toOAuthLoginButton = document.getElementById('toOAuthLoginButton');
    toLoginButton.addEventListener('click', async () => {
        const username = document.getElementById('usernameValue').value;
        const password = document.getElementById('passwordValue').value;
        await loginRequest(username, password, render, div);
    });
    toOAuthLoginButton.addEventListener('click', () => {
        redirectToIntraApi();
    });
};
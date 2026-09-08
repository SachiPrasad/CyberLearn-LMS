export interface User {
  id?: string | number;
  name: string;
  email: string;
  picture?: string;
}

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

export const authService = {
  async login(email: string, password: string): Promise<User> {
    if (!email || !password) {
      throw new Error("Email and password are required");
    }

    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Invalid credentials");
    }

    const data = await response.json();
    if (data.access_token) {
      localStorage.setItem("access_token", data.access_token);
    }

    return {
      id: data.user?.id || "u_" + Math.random().toString(36).substring(2, 9),
      name: data.user?.name || email.split('@')[0],
      email: data.user?.email || email,
    };
  },

  async register(name: string, email: string, password: string): Promise<User> {
    if (!name || !email || !password) {
      throw new Error("All fields are required");
    }

    const response = await fetch(`${API_URL}/api/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name, email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Registration failed");
    }

    const data = await response.json();
    if (data.access_token) {
      localStorage.setItem("access_token", data.access_token);
    }

    return {
      id: data.user?.id || "u_" + Math.random().toString(36).substring(2, 9),
      name: data.user?.name || name,
      email: data.user?.email || email,
    };
  },

  async googleAuth(profile: { email: string; name?: string; picture?: string; token?: string }): Promise<User> {
    const response = await fetch(`${API_URL}/api/auth/google`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(profile),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Google authentication failed on server");
    }

    const data = await response.json();
    if (data.access_token) {
      localStorage.setItem("access_token", data.access_token);
    }

    return {
      id: data.user?.id || "u_g_" + Math.random().toString(36).substring(2, 9),
      name: data.user?.name || profile.name || profile.email.split('@')[0],
      email: data.user?.email || profile.email,
      picture: profile.picture,
    };
  },
  
  logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("cyberlearn_user");
  }
};


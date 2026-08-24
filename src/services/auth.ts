export interface User {
  id: string;
  name: string;
  email: string;
}

// These are simulated API calls. 
// Replace these with actual fetch/axios requests to your VITE_AUTH_API_URL when ready.

export const authService = {
  async login(email: string, password: string): Promise<User> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 800));

    // Basic validation simulation
    if (!email || !password) {
      throw new Error("Email and password are required");
    }

    if (password.length < 6) {
      throw new Error("Invalid credentials");
    }

    // Mock successful response
    return {
      id: "u_" + Math.random().toString(36).substring(2, 9),
      name: email.split('@')[0],
      email: email,
    };
  },

  async register(name: string, email: string, password: string): Promise<User> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 800));

    if (!name || !email || !password) {
      throw new Error("All fields are required");
    }

    // Mock successful response
    return {
      id: "u_" + Math.random().toString(36).substring(2, 9),
      name: name,
      email: email,
    };
  }
};

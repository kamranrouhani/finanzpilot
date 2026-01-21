export interface User {
  id: string;
  username: string;
  created_at: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  password: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

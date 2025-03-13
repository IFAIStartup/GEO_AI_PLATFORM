import { User } from "./user";

export interface AuthResponse {
  access_token: string;
  user: User;
}

export interface ArcGISToken {
  token: string;
  expires: string;
  ssl: boolean;
}

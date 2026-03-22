const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  token?: string | null;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("prescient_token");
  }

  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = "GET", body, headers = {}, token } = options;
    const authToken = token ?? this.getToken();

    const config: RequestInit = {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        ...headers,
      },
    };

    if (body) {
      config.body = JSON.stringify(body);
    }

    const res = await fetch(`${this.baseUrl}${endpoint}`, config);

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new ApiError(res.status, error.detail || "Request failed");
    }

    return res.json();
  }

  // ── Health ──────────────────────────────────────────────────────
  async getHealth() {
    return this.request<HealthStatus>("/api/health");
  }

  // ── Discovery & Markets (from main.py) ──────────────────────────
  async getDiscovery() {
    return this.request<DiscoveryResponse>("/api/discovery");
  }

  async getMarkets() {
    return this.request<MarketsResponse>("/api/markets");
  }

  async getMarket(id: string) {
    return this.request<MarketDetail>(`/api/markets/${id}`);
  }

  async triggerCycle() {
    return this.request<Record<string, unknown>>("/api/agent/cycle", { method: "POST" });
  }

  async getReceipts(action?: string) {
    const params = action ? `?action=${action}` : "";
    return this.request<ReceiptsResponse>(`/api/receipts${params}`);
  }

  // ── Filecoin Storage (from main.py) ─────────────────────────────
  async getStorageRecord(cid: string) {
    return this.request<StorageResponse>(`/api/storage/${cid}`);
  }

  async getStorageIndex() {
    return this.request<StorageIndex>("/api/index");
  }

  // ── User Sync (Clerk → Backend) ─────────────────────────────────
  async syncUser(clerkId: string, username: string, email: string, displayName?: string) {
    return this.request<SyncResponse>("/api/users/sync", {
      method: "POST",
      body: { clerk_id: clerkId, username, email, display_name: displayName },
    });
  }

  async getProfile() {
    return this.request<ProfileResponse>("/api/users/me");
  }

  async updatePreferences(prefs: Record<string, unknown>) {
    return this.request<{ preferences: Record<string, unknown> }>("/api/users/preferences", {
      method: "PUT",
      body: prefs,
    });
  }

  async castVote(marketId: string, vote: "YES" | "NO", confidence = 0.5) {
    return this.request<Record<string, unknown>>("/api/users/vote", {
      method: "POST",
      body: { market_id: marketId, vote, confidence },
    });
  }

  async joinMarket(marketId: string, position = "WATCHING", amount = 0) {
    return this.request<Record<string, unknown>>("/api/users/join-market", {
      method: "POST",
      body: { market_id: marketId, position, amount },
    });
  }

  async attachWallet(walletAddress: string) {
    return this.request<{ user: Record<string, unknown>; wallet_attached: boolean }>("/api/users/wallet", {
      method: "PUT",
      body: { wallet_address: walletAddress },
    });
  }

  async getMyVotes() {
    return this.request<{ votes: Vote[]; count: number }>("/api/users/votes");
  }

  async getMyMarkets() {
    return this.request<{ markets: Record<string, unknown>[]; count: number }>("/api/users/markets");
  }

  async getActivity() {
    return this.request<{ activity: ActivityEntry[] }>("/api/users/activity");
  }

  // ── Market Data (from market_data.py) ───────────────────────────
  async getPrices() {
    return this.request<PricesResponse>("/api/data/prices");
  }

  async getPriceHistory(symbol: string, limit = 50) {
    return this.request<PriceHistoryResponse>(`/api/data/prices/${symbol}?limit=${limit}`);
  }

  async getSentiment(symbol?: string) {
    const params = symbol ? `?symbol=${symbol}` : "";
    return this.request<SentimentResponse>(`/api/data/sentiment${params}`);
  }

  async getTrackedCoins() {
    return this.request<{ coins: TrackedCoin[]; count: number }>("/api/data/coins");
  }

  async getRateLimits() {
    return this.request<Record<string, RateLimitStatus>>("/api/data/rate-limits");
  }

  async getSchedulerStatus() {
    return this.request<SchedulerStatus>("/api/data/scheduler/status");
  }

  async getSchedulerRuns(limit = 20) {
    return this.request<{ runs: SchedulerRun[]; count: number }>(`/api/data/scheduler/runs?limit=${limit}`);
  }

  async triggerAllJobs() {
    return this.request<Record<string, unknown>>("/api/data/scheduler/trigger", { method: "POST" });
  }

  async triggerPrices() {
    return this.request<Record<string, unknown>>("/api/data/scheduler/trigger/prices", { method: "POST" });
  }

  async triggerSentiment() {
    return this.request<Record<string, unknown>>("/api/data/scheduler/trigger/sentiment", { method: "POST" });
  }

  // ── Watchlist (protected) ───────────────────────────────────────
  async getWatchlist() {
    return this.request<WatchlistResponse>("/api/data/watchlist");
  }

  async setWatchlist(symbols: string[]) {
    return this.request<{ symbols: string[] }>("/api/data/watchlist", {
      method: "PUT",
      body: { symbols },
    });
  }

  async addToWatchlist(symbol: string) {
    return this.request<{ symbols: string[] }>(`/api/data/watchlist/${symbol}`, { method: "POST" });
  }

  async removeFromWatchlist(symbol: string) {
    return this.request<{ symbols: string[] }>(`/api/data/watchlist/${symbol}`, { method: "DELETE" });
  }

  // ── Public market data ──────────────────────────────────────────
  async getMarketProbability(marketId: string) {
    return this.request<MarketProbability>(`/api/markets/${marketId}/probability`);
  }

  async resolveMarket(marketId: string) {
    return this.request<Record<string, unknown>>(`/api/markets/${marketId}/resolve`, { method: "POST" });
  }

  async resolveExpiredMarkets() {
    return this.request<Record<string, unknown>>("/api/markets/resolve-expired", { method: "POST" });
  }

  async getMarketVotes(marketId: string) {
    return this.request<MarketVotes>(`/api/users/market-votes/${marketId}`);
  }

  async getMarketParticipants(marketId: string) {
    return this.request<MarketParticipants>(`/api/users/market-participants/${marketId}`);
  }
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

// ── Types ──────────────────────────────────────────────────────────

export interface HealthStatus {
  status: string;
  timestamp: string;
  dune: string;
  uniswap: string;
  lighthouse: string;
  twitter: string;
  scheduler: string;
  [key: string]: string;  // allow extra fields
}

export interface DiscoveryResponse {
  events: DiscoveryEvent[];
  events_count: number;
  timestamp: string;
  message?: string;
}

export interface DiscoveryEvent {
  event_id: string;
  event_type: string;
  protocol: string;
  description: string;
  metric_value: number;
  metric_change_pct: number;
  sentiment_score?: number;
  tradability_score?: number;
  chain: string;
}

export interface MarketsResponse {
  markets: MarketDetail[];
  count: number;
}

export interface MarketDetail {
  market_id: string;
  question: string;
  resolution_criteria: string;
  deadline: string;
  status: string;
  contract_address?: string;
  pool_address?: string;
  discovery_cid?: string;
  evidence_cids?: string[];
  participants?: number;
  total_volume?: number;
  yes_probability?: number;
}

export interface ReceiptsResponse {
  receipts: Receipt[];
  count: number;
}

export interface Receipt {
  action: string;
  agent_address?: string;
  signature?: string;
  payload_hash?: string;
  related_cids?: string[];
  timestamp?: string;
}

export interface StorageResponse {
  data: Record<string, unknown>;
  cid: string;
  timestamp: string;
}

export interface StorageIndex {
  version: number;
  updated_at: string;
  markets: Record<string, string[]>;
  latest_discovery_cid?: string;
  latest_index_cid?: string;
}

export interface SyncResponse {
  user: Record<string, unknown>;
  token: string;
  filecoin_cid: string | null;
  synced: boolean;
}

export interface ProfileResponse {
  user: Record<string, unknown>;
  preferences: Record<string, unknown>;
}

export interface Vote {
  id: number;
  market_id: string;
  vote: string;
  confidence: number;
  created_at: string;
}

export interface ActivityEntry {
  id: number;
  action: string;
  details: string;
  created_at: string;
}

export interface PricesResponse {
  prices: PriceEntry[];
  count: number;
}

export interface PriceEntry {
  symbol: string;
  name?: string;
  price_usd: number;
  change_24h: number;
  volume_24h: number;
  market_cap: number;
  updated_at: string;
}

export interface PriceHistoryResponse {
  symbol: string;
  history: PriceHistoryPoint[];
  count: number;
}

export interface PriceHistoryPoint {
  price_usd: number;
  volume_24h: number;
  market_cap: number;
  recorded_at: string;
}

export interface SentimentResponse {
  sentiment: SentimentEntry[];
  count: number;
}

export interface SentimentEntry {
  symbol: string;
  source: string;
  score: number;
  mention_count: number;
  positive_count: number;
  negative_count: number;
  sample_texts?: string[];
  recorded_at: string;
}

export interface TrackedCoin {
  symbol: string;
  name: string;
  coingecko_id: string;
  added_at: string;
}

export interface RateLimitStatus {
  name: string;
  requests_remaining: number;
  daily_remaining: number;
  window_resets_in: number;
}

export interface SchedulerStatus {
  running: boolean;
  jobs: Record<string, { last_run?: string; next_run?: string; interval_hours: number }>;
  errors?: string[];
}

export interface SchedulerRun {
  job_name: string;
  status: string;
  started_at: string;
  completed_at?: string;
  records_fetched?: number;
  error?: string;
}

export interface WatchlistResponse {
  symbols: string[];
  prices: PriceEntry[];
  sentiment: SentimentEntry[];
}

export interface MarketProbability {
  market_id: string;
  yes_probability: number;
  no_probability: number;
  components: {
    dune: { score: number; weight: number; detail: string };
    sentiment: { score: number; weight: number; detail: string };
  };
  recommendation: "YES" | "NO" | "UNCERTAIN";
  calculated_at: string;
}

export interface MarketVotes {
  market_id: string;
  YES: number;
  NO: number;
  yes_confidence: number;
  no_confidence: number;
  total_votes: number;
}

export interface MarketParticipants {
  market_id: string;
  participants: { username: string; position: string; amount: number }[];
  count: number;
}

export const api = new ApiClient(API_BASE);

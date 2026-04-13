import axios from "axios";
import { toast } from "sonner";

const MAX_RETRIES = 3;
const BASE_DELAY = 2000;

const isRetryable = (error) => {
  const status = error.response?.status;
  return status === 503 || status === 520 || error.code === "ECONNABORTED" || !error.response;
};

axios.interceptors.response.use(null, async (error) => {
  const config = error.config;
  if (!config) return Promise.reject(error);

  config.__retryCount = config.__retryCount || 0;

  const isGet = (config.method || "get").toLowerCase() === "get";
  if (!isGet || !isRetryable(error) || config.__retryCount >= MAX_RETRIES) {
    if (config.__retryCount >= MAX_RETRIES) {
      toast.dismiss("api-retry");
      toast.error("Unable to connect. Please refresh or try again later.", { duration: 4000 });
    }
    return Promise.reject(error);
  }

  config.__retryCount += 1;
  const delay = BASE_DELAY * Math.pow(2, config.__retryCount - 1);

  if (config.__retryCount === 1) {
    toast.loading("Reconnecting...", { id: "api-retry", duration: Infinity });
  }

  await new Promise((r) => setTimeout(r, delay));
  return axios(config);
});

axios.interceptors.response.use(
  (response) => {
    if (response.config?.__retryCount > 0) {
      toast.dismiss("api-retry");
      toast.success("Connected!", { duration: 1500 });
    }
    return response;
  },
  (error) => Promise.reject(error)
);

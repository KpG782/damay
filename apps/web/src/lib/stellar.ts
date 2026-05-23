import { env } from "./env";

const NETWORK = env.NEXT_PUBLIC_STELLAR_NETWORK;

export function stellarExpertTxUrl(hash: string): string {
  return `https://stellar.expert/explorer/${NETWORK}/tx/${hash}`;
}

export function stellarExpertContractUrl(contractId: string): string {
  return `https://stellar.expert/explorer/${NETWORK}/contract/${contractId}`;
}

export function stellarExpertAccountUrl(account: string): string {
  return `https://stellar.expert/explorer/${NETWORK}/account/${account}`;
}

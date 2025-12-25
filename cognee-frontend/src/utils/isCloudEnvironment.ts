
export default function isCloudEnvironment() {
  const envValue = process.env.NEXT_PUBLIC_IS_CLOUD_ENVIRONMENT ?? "false";
  return envValue.toLowerCase() === "true";
}

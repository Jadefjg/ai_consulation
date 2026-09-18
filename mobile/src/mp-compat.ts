// 微信基础库 3.7+ 把 getSystemInfo 标成兼容 API。
// 在框架调用前改走拆分接口，减少开发者工具里的 HarmonyOS 提示。
// #ifdef MP-WEIXIN
type SysInfoCallback = (res: Record<string, unknown>) => void

try {
  const api = (globalThis as { wx?: Record<string, any> }).wx
  if (api && typeof api.getDeviceInfo === 'function' && !api.__aiMedicalPatchedSysInfo) {
    api.__aiMedicalPatchedSysInfo = true
    const assemble = () => ({
      ...api.getDeviceInfo(),
      ...api.getWindowInfo(),
      ...api.getAppBaseInfo(),
      errMsg: 'getSystemInfo:ok',
    })
    api.getSystemInfoSync = assemble
    api.getSystemInfo = (opts: { success?: SysInfoCallback; complete?: SysInfoCallback; fail?: SysInfoCallback } = {}) => {
      try {
        const res = assemble()
        opts.success?.(res)
        opts.complete?.(res)
      } catch (error) {
        const payload = (error || {}) as Record<string, unknown>
        opts.fail?.(payload)
        opts.complete?.(payload)
      }
    }
  }
} catch {
  /* 旧基础库没有拆分 API 时保持原生实现 */
}
// #endif

export {}

export const getTimeDifference = (timeDifference: number) => {
    // 将时间差转换为秒
    const totalSeconds = Math.floor(timeDifference / 1000);
    // 计算小时、分钟和秒
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    // 返回格式化的时、分、秒字符串
    return {
        hours,
        minutes,
        seconds
    }
}
import React, { useEffect, useRef, useState } from 'react';

interface CountUpProps {
    end: number;
    duration?: number;
    suffix?: string;
    prefix?: string;
    separator?: string;
}

export const CountUp: React.FC<CountUpProps> = ({
    end,
    duration = 2000,
    suffix = '',
    prefix = '',
    separator = ','
}) => {
    const [count, setCount] = useState(0);
    const elementRef = useRef<HTMLDivElement>(null);
    const hasAnimated = useRef(false);

    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                const [entry] = entries;
                if (entry.isIntersecting && !hasAnimated.current) {
                    hasAnimated.current = true;

                    let startTime: number | null = null;
                    const startValue = 0;

                    const animate = (timestamp: number) => {
                        if (!startTime) startTime = timestamp;
                        const progress = timestamp - startTime;
                        const percentage = Math.min(progress / duration, 1);

                        // Easing function: easeOutQuart
                        const ease = 1 - Math.pow(1 - percentage, 4);

                        const currentCount = Math.floor(startValue + (end - startValue) * ease);
                        setCount(currentCount);

                        if (progress < duration) {
                            requestAnimationFrame(animate);
                        } else {
                            setCount(end);
                        }
                    };

                    requestAnimationFrame(animate);
                }
            },
            { threshold: 0.1 }
        );

        if (elementRef.current) {
            observer.observe(elementRef.current);
        }

        return () => {
            if (elementRef.current) {
                observer.unobserve(elementRef.current);
            }
        };
    }, [end, duration]);

    const formattedCount = count.toString().replace(/\B(?=(\d{3})+(?!\d))/g, separator);

    return (
        <span ref={elementRef}>
            {prefix}{formattedCount}{suffix}
        </span>
    );
};

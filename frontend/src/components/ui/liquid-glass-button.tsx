'use client';

// Adapted from the supplied LiquidButton/MetalButton source. The basic Button
// shares the enhanced implementation; Slot supports an actual anchor asChild.
import * as React from 'react';
import { Slot, Slottable } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import './liquid-glass-button.css';
// Preserve the supplied public API while sharing one basic Button implementation.
// eslint-disable-next-line react/only-export-components
export { Button, buttonVariants } from './button';

const liquidbuttonVariants = cva(
  'liquid-button relative inline-flex shrink-0 cursor-pointer items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm font-medium outline-none disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0',
  {
    variants: {
      variant: {
        default: 'bg-transparent text-primary',
        destructive: 'bg-destructive text-white',
        outline: 'border border-input bg-background text-foreground',
        secondary: 'bg-secondary text-secondary-foreground',
        ghost: 'text-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-9 px-4 py-2', sm: 'h-8 gap-1.5 px-4 text-xs',
        lg: 'h-10 px-6', xl: 'h-12 px-8', xxl: 'h-14 px-10', icon: 'size-9',
      },
    },
    defaultVariants: { variant: 'default', size: 'xxl' },
  },
);
type LiquidButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof liquidbuttonVariants> & { asChild?: boolean };

const LiquidButton = React.forwardRef<HTMLButtonElement, LiquidButtonProps>(
  ({ className, variant, size, asChild = false, children, style, ...props }, ref) => {
    const filterId = `liquid-glass-${React.useId().replace(/[^a-zA-Z0-9_-]/g, '')}`;
    const Comp = asChild ? Slot : 'button';
    const label = <span className="liquid-button__label">{asChild ? (children as React.ReactElement<{ children?: React.ReactNode }>).props.children : children}</span>;
    const content = asChild
      ? React.cloneElement(React.Children.only(children) as React.ReactElement<{ children?: React.ReactNode }>, {}, label)
      : label;
    return <Comp ref={ref} data-slot="button" className={cn(liquidbuttonVariants({ variant, size, className }))}
      style={{ '--liquid-filter': `url("#${filterId}")`, ...style } as React.CSSProperties} {...props}>
      <span aria-hidden="true" className="liquid-button__backdrop" />
      <span aria-hidden="true" className="liquid-button__rim" />
      <Slottable>{content}</Slottable>
      <GlassFilter id={filterId} />
    </Comp>;
  },
);
LiquidButton.displayName = 'LiquidButton';

function GlassFilter({ id }: { id: string }) {
  return <svg className="liquid-button__filter" aria-hidden="true" focusable="false" width="0" height="0">
    <defs><filter id={id} x="0%" y="0%" width="100%" height="100%" colorInterpolationFilters="sRGB">
      <feTurbulence type="fractalNoise" baseFrequency="0.05 0.05" numOctaves="1" seed="1" result="turbulence" />
      <feGaussianBlur in="turbulence" stdDeviation="2" result="blurredNoise" />
      <feDisplacementMap in="SourceGraphic" in2="blurredNoise" scale="70" xChannelSelector="R" yChannelSelector="B" result="displaced" />
      <feGaussianBlur in="displaced" stdDeviation="4" result="finalBlur" />
      <feComposite in="finalBlur" in2="finalBlur" operator="over" />
    </filter></defs>
  </svg>;
}

type ColorVariant = 'default' | 'primary' | 'success' | 'error' | 'gold' | 'bronze';
interface MetalButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> { variant?: ColorVariant }
const colorVariants: Record<ColorVariant, { outer: string; inner: string; button: string; textColor: string; textShadow: string }> = {
  default: { outer: 'bg-gradient-to-b from-[#000] to-[#A0A0A0]', inner: 'bg-gradient-to-b from-[#FAFAFA] via-[#3E3E3E] to-[#E5E5E5]', button: 'bg-gradient-to-b from-[#B9B9B9] to-[#969696]', textColor: 'text-white', textShadow: '[text-shadow:0_-1px_0_rgb(80_80_80/100%)]' },
  primary: { outer: 'bg-gradient-to-b from-[#000] to-[#A0A0A0]', inner: 'bg-gradient-to-b from-primary via-secondary to-muted', button: 'bg-gradient-to-b from-primary to-primary/40', textColor: 'text-white', textShadow: '[text-shadow:0_-1px_0_rgb(30_58_138/100%)]' },
  success: { outer: 'bg-gradient-to-b from-[#005A43] to-[#7CCB9B]', inner: 'bg-gradient-to-b from-[#E5F8F0] via-[#00352F] to-[#D1F0E6]', button: 'bg-gradient-to-b from-[#9ADBC8] to-[#3E8F7C]', textColor: 'text-[#FFF7F0]', textShadow: '[text-shadow:0_-1px_0_rgb(6_78_59/100%)]' },
  error: { outer: 'bg-gradient-to-b from-[#5A0000] to-[#FFAEB0]', inner: 'bg-gradient-to-b from-[#FFDEDE] via-[#680002] to-[#FFE9E9]', button: 'bg-gradient-to-b from-[#F08D8F] to-[#A45253]', textColor: 'text-[#FFF7F0]', textShadow: '[text-shadow:0_-1px_0_rgb(146_64_14/100%)]' },
  gold: { outer: 'bg-gradient-to-b from-[#917100] to-[#EAD98F]', inner: 'bg-gradient-to-b from-[#FFFDDD] via-[#856807] to-[#FFF1B3]', button: 'bg-gradient-to-b from-[#FFEBA1] to-[#9B873F]', textColor: 'text-[#FFFDE5]', textShadow: '[text-shadow:0_-1px_0_rgb(178_140_2/100%)]' },
  bronze: { outer: 'bg-gradient-to-b from-[#864813] to-[#E9B486]', inner: 'bg-gradient-to-b from-[#EDC5A1] via-[#5F2D01] to-[#FFDEC1]', button: 'bg-gradient-to-b from-[#FFE3C9] to-[#A36F3D]', textColor: 'text-[#FFF7F0]', textShadow: '[text-shadow:0_-1px_0_rgb(124_45_18/100%)]' },
};

const MetalButton = React.forwardRef<HTMLButtonElement, MetalButtonProps>(
  ({ children, className, variant = 'default', onPointerDown, onPointerUp, onPointerLeave, onPointerEnter, onPointerCancel, onBlur, style, ...props }, ref) => {
    const [pressed, setPressed] = React.useState(false);
    const [hovered, setHovered] = React.useState(false);
    const colors = colorVariants[variant];
    return <span className={cn('metal-button relative inline-flex rounded-md p-[1.25px]', colors.outer)} data-pressed={pressed || undefined}>
      <span aria-hidden="true" className={cn('pointer-events-none absolute inset-px rounded-lg', colors.inner)} />
      <button ref={ref} {...props} className={cn('relative z-10 m-px inline-flex h-11 items-center justify-center overflow-hidden rounded-md px-6 py-2 text-sm font-semibold', colors.button, colors.textColor, colors.textShadow, className)} style={style}
        onPointerDown={event => { if (!props.disabled) setPressed(true); onPointerDown?.(event); }}
        onPointerUp={event => { setPressed(false); onPointerUp?.(event); }}
        onPointerCancel={event => { setPressed(false); onPointerCancel?.(event); }}
        onPointerLeave={event => { setPressed(false); setHovered(false); onPointerLeave?.(event); }}
        onPointerEnter={event => { setHovered(event.pointerType !== 'touch'); onPointerEnter?.(event); }}
        onBlur={event => { setPressed(false); onBlur?.(event); }}>
        <span aria-hidden="true" className={cn('pointer-events-none absolute inset-0 rounded-md bg-gradient-to-r from-transparent via-neutral-100 to-transparent transition-opacity duration-300', pressed ? 'opacity-20' : 'opacity-0')} />
        {children || 'Button'}
        {hovered && !pressed && <span aria-hidden="true" className="pointer-events-none absolute inset-0 rounded-md bg-gradient-to-t from-transparent to-white/5" />}
      </button>
    </span>;
  },
);
MetalButton.displayName = 'MetalButton';
// eslint-disable-next-line react/only-export-components
export { liquidbuttonVariants, LiquidButton, MetalButton };

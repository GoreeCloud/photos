<script lang="ts">
  type Props = {
    variant?: 'icon' | 'wordmark';
    class?: string;
    alt?: string;
  };

  let { variant = 'wordmark', class: className = '', alt = 'GoreeCloud Photos' }: Props = $props();
</script>

{#if variant === 'icon'}
  <img src="/icon.svg" {alt} class={className} width="128" height="128" />
{:else}
  <img
    src="/goreecloud-photos-logo.svg"
    {alt}
    class={className + ' dark:hidden'}
    width="668"
    height="156"
  />
  <img
    src="/goreecloud-photos-logo-dark.svg"
    {alt}
    class={className + ' hidden dark:block'}
    width="668"
    height="156"
  />
{/if}

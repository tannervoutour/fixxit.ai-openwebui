<script lang="ts">
	import { goto } from '$app/navigation';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import Logs from '$lib/components/icons/Logs.svelte';
	import Search from '$lib/components/icons/Search.svelte';
	import { WEBUI_BASE_URL } from '$lib/constants';
	import { showSearch } from '$lib/stores';

	let selected = '';
</script>

<div class="min-w-[4.5rem] bg-gray-50 dark:bg-gray-950 flex gap-2.5 flex-col pt-8">
	<div class="flex justify-center relative">
		{#if selected === 'home'}
			<div class="absolute top-0 left-0 flex h-full">
				<div class="my-auto rounded-r-lg w-1 h-8 bg-black dark:bg-white"></div>
			</div>
		{/if}

		<Tooltip content="Home" placement="right">
			<button
				class=" cursor-pointer {selected === 'home' ? 'rounded-2xl' : 'rounded-full'}"
				on:click={() => {
					selected = 'home';

					if (window.electronAPI) {
						window.electronAPI.load('home');
					}
				}}
			>
				<img
					src="{WEBUI_BASE_URL}/static/splash.png"
					class="size-11 dark:invert p-0.5"
					alt="logo"
					draggable="false"
				/>
			</button>
		</Tooltip>
	</div>

	<div class=" -mt-1 border-[1.5px] border-gray-100 dark:border-gray-900 mx-4"></div>

	<div class="flex justify-center relative group">
		{#if selected === ''}
			<div class="absolute top-0 left-0 flex h-full">
				<div class="my-auto rounded-r-lg w-1 h-8 bg-black dark:bg-white"></div>
			</div>
		{/if}
		<button
			class=" cursor-pointer bg-transparent"
			on:click={() => {
				selected = '';
			}}
		>
			<img
				src="{WEBUI_BASE_URL}/static/favicon.png"
				class="size-10 {selected === '' ? 'rounded-2xl' : 'rounded-full'}"
				alt="logo"
				draggable="false"
			/>
		</button>
	</div>

	<!-- Search Button -->
	<div class="flex justify-center relative group text-gray-400">
		<Tooltip content="Search" placement="right">
			<button
				class="cursor-pointer p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-900 transition"
				on:click={() => showSearch.set(true)}
			>
				<Search className="size-5" strokeWidth="2" />
			</button>
		</Tooltip>
	</div>

	<!-- Logs Button -->
	<div class="flex justify-center relative group text-gray-400">
		<Tooltip content="Logs" placement="right">
			<button
				class="cursor-pointer p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-900 transition"
				on:click={() => goto('/logs')}
			>
				<Logs className="size-5" strokeWidth="2" />
			</button>
		</Tooltip>
	</div>
</div>

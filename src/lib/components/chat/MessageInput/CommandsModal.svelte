<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	
	const dispatch = createEventDispatcher();
	
	export let show = false;
	export let onClose = () => {};
	
	const availableCommands = [
		{
			command: '/log',
			description: 'Access the specialized logs agent for log-related assistance and creation',
			color: 'green'
		},
		{
			command: '/help',
			description: 'Access the help agent for assistance and documentation',
			color: 'blue'
		}
	];
	
	const handleCommandSelect = (command: string) => {
		dispatch('command-select', { command });
		show = false;
		onClose();
	};
	
	const handleKeydown = (event: KeyboardEvent, command: string) => {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			handleCommandSelect(command);
		}
	};
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<!-- svelte-ignore a11y-no-static-element-interactions -->
{#if show}
	<div
		class="absolute bottom-full mb-2 left-0 z-50"
		on:click|stopPropagation
	>
		<div
			class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg min-w-80 max-w-96"
		>
			<div class="p-3 border-b border-gray-200 dark:border-gray-700">
				<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Available Commands</h3>
				<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Select a command to access specialized agents</p>
			</div>
			
			<div class="p-2">
				{#each availableCommands as { command, description, color }}
					<!-- svelte-ignore a11y-click-events-have-key-events -->
					<!-- svelte-ignore a11y-no-static-element-interactions -->
					<div
						class="flex items-start gap-3 p-3 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors group"
						on:click={() => handleCommandSelect(command)}
						on:keydown={(e) => handleKeydown(e, command)}
						tabindex="0"
						role="button"
						aria-label="Select {command} command"
					>
						<div
							class="flex-shrink-0 w-2 h-2 rounded-full mt-2 {color === 'green' 
								? 'bg-green-500' 
								: 'bg-blue-500'}"
						></div>
						
						<div class="flex-1 min-w-0">
							<div class="flex items-center gap-2">
								<code class="text-sm font-mono px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-gray-800 dark:text-gray-200">
									{command}
								</code>
							</div>
							<p class="text-sm text-gray-600 dark:text-gray-300 mt-1 leading-relaxed">
								{description}
							</p>
						</div>
						
						<div class="opacity-0 group-hover:opacity-100 transition-opacity">
							<svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
							</svg>
						</div>
					</div>
				{/each}
			</div>
		</div>
	</div>
{/if}
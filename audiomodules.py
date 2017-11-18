import sys
import audioio as ai
        
if __name__ == "__main__":
    print('')
    print('Status of audio packages on this machine:')
    print('-'*41)
    print('')
    ai.list_modules()
    print('')
    ai.missing_modules_instructions()
    print('')

    if len(sys.argv) > 1 :
        mod = sys.argv[1]
        if mod in ai.audiomodules.audio_modules:
            print('Installation instructions for the %s module:' % mod )
            print('-'*(42+len(mod)))
            print(ai.installation_instruction(mod))
            print('')
